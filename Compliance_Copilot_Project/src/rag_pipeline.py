"""
rag_pipeline.py
---------------
FR5 + FR7 + FR8  (Q&A, Generation, Citations)

FIXES in this version:
  1. Score threshold — only show sources with score > MIN_SCORE.
     Low-relevance chunks are retrieved for context but NOT shown as citations.
     This stops irrelevant pages appearing in the sources panel.

  2. No citations on "not found" answers — if the LLM says it could not find
     the information, sources are cleared so the UI shows no citations.

  3. Dynamic citation count — instead of always showing exactly TOP_K sources,
     only sources that actually contributed to the answer are shown.
"""
from __future__ import annotations

import logging
import textwrap
import traceback
from dataclasses import dataclass, field
from typing import List, Optional

from src.config import (
    MAX_NEW_TOKENS, PHI2_MODEL_NAME, TEMPERATURE,
    TOP_K_RESULTS, VECTORSTORE_DIR,
)
from src.vector_store import ComplianceVectorStore

logger = logging.getLogger(__name__)

# Only show a source as a citation if its score is above this threshold.
# Scores below this mean the chunk wasn't actually relevant to the question.
MIN_CITATION_SCORE = 0.15

# Phrases that indicate the LLM could not find the answer
NOT_FOUND_PHRASES = [
    "could not find",
    "not found in",
    "not available in",
    "no information",
    "not mentioned",
    "not specified",
    "outside the scope",
    "not covered",
    "i don't know",
    "i do not know",
]


@dataclass
class CitedSource:
    document_name:   str
    page_number:     int
    excerpt:         str
    relevance_score: float


@dataclass
class RAGResponse:
    question:    str
    answer:      str
    sources:     List[CitedSource] = field(default_factory=list)
    has_context: bool = True
    error:       str  = ""

    def format_sources(self) -> str:
        if not self.sources:
            return "No sources found."
        lines = []
        for i, s in enumerate(self.sources, 1):
            lines.append(
                f"[{i}] {s.document_name}  |  Page {s.page_number}\n"
                f"    ...{s.excerpt}..."
            )
        return "\n".join(lines)


def _answer_is_not_found(answer: str) -> bool:
    """Return True if the answer indicates the info wasn't in the documents."""
    a = answer.lower()
    return any(phrase in a for phrase in NOT_FOUND_PHRASES)


class ComplianceRAGPipeline:

    def __init__(
        self,
        vectorstore:    Optional[ComplianceVectorStore] = None,
        top_k:          int   = TOP_K_RESULTS,
        model_name:     str   = PHI2_MODEL_NAME,
        max_new_tokens: int   = MAX_NEW_TOKENS,
        temperature:    float = TEMPERATURE,
    ):
        self.top_k          = top_k
        self.model_name     = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature    = temperature
        self.vectorstore    = vectorstore or ComplianceVectorStore(persist_dir=VECTORSTORE_DIR)
        self._llm           = None
        self._llm_error     = ""

    def _get_llm(self):
        if self._llm is not None:
            return self._llm
        if self._llm_error:
            raise RuntimeError(self._llm_error)
        try:
            from src.llm_engine import get_llm
            self._llm = get_llm(
                model_name=self.model_name,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            return self._llm
        except Exception as exc:
            self._llm_error = str(exc)
            raise

    def _fallback_answer(self, results) -> str:
        lines = ["⚠️ Language model unavailable — showing matching policy excerpts:\n"]
        for i, (doc, score) in enumerate(results, 1):
            lines.append(
                f"Excerpt {i} (Page {doc.metadata.get('page','?')}):\n"
                f"{doc.page_content.strip()}\n"
            )
        return "\n".join(lines)

    def query(self, question: str) -> RAGResponse:
        question = question.strip()
        if not question:
            return RAGResponse(question=question,
                               answer="Please enter a question.",
                               has_context=False)

        # ── Step 1: Retrieve ──────────────────────────────────────────────────
        try:
            results = self.vectorstore.similarity_search(question, k=self.top_k)
        except RuntimeError as exc:
            return RAGResponse(
                question=question, has_context=False,
                answer="⚠️ No documents indexed yet. Upload a PDF first.",
                error=str(exc),
            )

        if not results:
            return RAGResponse(
                question=question, sources=[],
                answer="I could not find any relevant information in the policy documents.",
            )

        # ── Step 2: Build context (use ALL retrieved chunks for LLM context) ──
        # But only mark HIGH-SCORE chunks as citations for the user to see.
        context_parts   = []
        all_sources     = []   # all retrieved, for context
        cited_sources   = []   # only high-score, shown as citations

        for rank, (doc, score) in enumerate(results, 1):
            meta    = doc.metadata
            excerpt = textwrap.shorten(doc.page_content, width=200, placeholder="...")

            context_parts.append(
                f"[Source {rank}: {meta.get('source','unknown')},"
                f" Page {meta.get('page','?')}]\n{doc.page_content}"
            )

            source = CitedSource(
                document_name=meta.get("source", "Unknown"),
                page_number=meta.get("page", 0),
                excerpt=excerpt,
                relevance_score=score,
            )
            all_sources.append(source)

            # Only cite if score is above threshold
            if score >= MIN_CITATION_SCORE:
                cited_sources.append(source)

        context = "\n\n---\n\n".join(context_parts)

        # ── Step 3: Generate answer ───────────────────────────────────────────
        try:
            from src.llm_engine import build_prompt
            prompt = build_prompt(context=context, question=question)
            llm    = self._get_llm()
            answer = llm.generate(prompt)

            if not answer or not answer.strip():
                answer = self._fallback_answer(results)

        except Exception as exc:
            logger.error("LLM failed: %s\n%s", exc, traceback.format_exc())
            return RAGResponse(
                question=question,
                answer=self._fallback_answer(results),
                sources=cited_sources,
                has_context=True,
                error=f"{type(exc).__name__}: {exc}",
            )

        # ── Step 4: Decide whether to show citations ──────────────────────────
        # If the answer says "not found", clear citations — nothing relevant was found.
        if _answer_is_not_found(answer):
            final_sources = []
        else:
            final_sources = cited_sources

        return RAGResponse(
            question=question,
            answer=answer,
            sources=final_sources,
            has_context=True,
        )

    def ingest_pdf(self, pdf_path, chunk_size=None, chunk_overlap=None):
        from pathlib import Path
        from src.config import CHUNK_OVERLAP, CHUNK_SIZE
        from src.document_processor import load_and_chunk_pdf
        chunks = load_and_chunk_pdf(
            Path(pdf_path),
            chunk_size    = chunk_size    or CHUNK_SIZE,
            chunk_overlap = chunk_overlap or CHUNK_OVERLAP,
        )
        self.vectorstore.add_documents(chunks)
        return len(chunks)
