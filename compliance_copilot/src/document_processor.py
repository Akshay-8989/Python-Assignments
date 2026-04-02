"""
document_processor.py
---------------------
FR1 – Document Upload
FR2 – Document Processing: text + EasyOCR image extraction + chunking

BUG FIX in this version:
  pdfplumber stores image coordinates in PDF space where y=0 is at the BOTTOM
  of the page. But page.crop() expects coordinates where y=0 is at the TOP.
  The old code passed the raw PDF coords directly to crop() which caused it to
  crop the wrong area (text below the image instead of the image itself).

  Fix: convert y coordinates before cropping:
    crop_y0 = page.height - img['y1']
    crop_y1 = page.height - img['y0']
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class DocumentChunk:
    text:        str
    source_file: str
    page_number: int
    chunk_index: int
    doc_hash:    str
    chunk_type:  str  = "text"
    metadata:    dict = field(default_factory=dict)


# ── Text utilities ────────────────────────────────────────────────────────────

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _clean_text(raw: str) -> str:
    text = raw.replace("\x00", "")
    text = re.sub(r"[\r\n]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "--")
    return text.strip()


def _split_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break
        search_start = max(start, end - chunk_size // 5)
        boundary = max(
            text.rfind(". ", search_start, end),
            text.rfind(".\n", search_start, end),
            text.rfind("\n\n", search_start, end),
        )
        if boundary != -1:
            end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap
    return chunks


# ── EasyOCR setup ─────────────────────────────────────────────────────────────

_easyocr_reader      = None
_ocr_available_cache: Optional[bool] = None


def _get_ocr_reader():
    global _easyocr_reader
    if _easyocr_reader is not None:
        return _easyocr_reader
    try:
        import easyocr
        from src.config import EASYOCR_LANGUAGES
        logger.info("Initialising EasyOCR (may download model ~100 MB on first run)…")
        _easyocr_reader = easyocr.Reader(EASYOCR_LANGUAGES, gpu=False, verbose=False)
        logger.info("EasyOCR ready.")
        return _easyocr_reader
    except Exception as e:
        logger.warning("EasyOCR unavailable: %s", e)
        return None


def _ocr_available() -> bool:
    global _ocr_available_cache
    if _ocr_available_cache is None:
        try:
            import easyocr  # noqa: F401
            _ocr_available_cache = True
        except ImportError:
            _ocr_available_cache = False
            logger.warning(
                "easyocr not installed. Image text extraction disabled. "
                "Run:  pip install easyocr"
            )
    return _ocr_available_cache


# ── Image extraction — FIXED coordinate conversion ───────────────────────────

def _images_from_page(page) -> List[bytes]:
    """
    Extract PNG bytes for each image on a pdfplumber page.

    KEY FIX: pdfplumber image coordinates use PDF space where y=0 is at the
    BOTTOM of the page. page.crop() uses screen/top-left space where y=0 is
    at the TOP. Without converting, crop() grabs the wrong area entirely.

    Conversion:
        crop_y0 = page.height - img['y1']   (top of image in screen coords)
        crop_y1 = page.height - img['y0']   (bottom of image in screen coords)
    """
    images_bytes = []
    try:
        page_h = page.height

        for img in page.images:
            try:
                # Raw PDF coordinates (y=0 at bottom)
                pdf_x0 = img["x0"]
                pdf_y0 = img["y0"]
                pdf_x1 = img["x1"]
                pdf_y1 = img["y1"]

                # Skip tiny images (decorative borders, icons)
                if (pdf_x1 - pdf_x0) < 50 or abs(pdf_y1 - pdf_y0) < 50:
                    continue

                # Convert to top-left origin for page.crop()
                crop_x0 = pdf_x0
                crop_y0 = page_h - pdf_y1   # ← THE FIX
                crop_x1 = pdf_x1
                crop_y1 = page_h - pdf_y0   # ← THE FIX

                # Guard against negative or inverted coords
                if crop_y0 < 0:
                    crop_y0 = 0
                if crop_y1 > page_h:
                    crop_y1 = page_h
                if crop_y0 >= crop_y1:
                    logger.debug("Skipping image with invalid crop coords")
                    continue

                cropped   = page.crop((crop_x0, crop_y0, crop_x1, crop_y1))
                pil_image = cropped.to_image(resolution=300).original

                import io
                buf = io.BytesIO()
                pil_image.save(buf, format="PNG")
                images_bytes.append(buf.getvalue())
                logger.debug(
                    "Extracted image: crop=(%d,%d,%d,%d) size=%dx%d",
                    crop_x0, crop_y0, crop_x1, crop_y1,
                    pil_image.width, pil_image.height
                )

            except Exception as e:
                logger.debug("Could not extract image from page: %s", e)

    except Exception as e:
        logger.debug("Image extraction skipped for page: %s", e)

    return images_bytes


def _ocr_image_bytes(img_bytes: bytes) -> str:
    """Run EasyOCR on PNG bytes. Returns extracted text."""
    reader = _get_ocr_reader()
    if reader is None:
        return ""
    try:
        import numpy as np
        from PIL import Image
        import io

        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        np_img  = np.array(pil_img)

        results = reader.readtext(np_img, detail=0, paragraph=True)
        text    = " ".join(str(r) for r in results)
        return _clean_text(text)
    except Exception as e:
        logger.debug("OCR failed for image: %s", e)
        return ""


# ── Page extraction ───────────────────────────────────────────────────────────

def _extract_pages(pdf_path: Path):
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text      = page.extract_text() or ""
                ocr_texts = []
                if _ocr_available():
                    for img_bytes in _images_from_page(page):
                        ocr_text = _ocr_image_bytes(img_bytes)
                        if ocr_text and len(ocr_text) > 20:
                            ocr_texts.append(ocr_text)
                yield i, text, ocr_texts
    except ImportError:
        logger.warning("pdfplumber not found — falling back to pypdf (no image extraction).")
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages, start=1):
            yield i, (page.extract_text() or ""), []


# ── Public API ────────────────────────────────────────────────────────────────

def load_and_chunk_pdf(
    pdf_path:      Path,
    chunk_size:    int = 512,
    chunk_overlap: int = 64,
) -> List[DocumentChunk]:
    """
    PDF → text + OCR images → clean → chunk → DocumentChunk list.
    Image OCR now correctly crops the actual image region (y-axis bug fixed).
    """
    logger.info("Processing PDF: %s", pdf_path.name)
    doc_hash    = _file_hash(pdf_path)
    all_chunks: List[DocumentChunk] = []
    text_count  = 0
    ocr_count   = 0

    for page_no, raw_text, ocr_texts in _extract_pages(pdf_path):

        # Text chunks
        clean = _clean_text(raw_text)
        if clean:
            text_count += 1
            for idx, chunk in enumerate(
                _split_into_chunks(clean, chunk_size, chunk_overlap)
            ):
                all_chunks.append(DocumentChunk(
                    text=chunk,
                    source_file=pdf_path.name,
                    page_number=page_no,
                    chunk_index=idx,
                    doc_hash=doc_hash,
                    chunk_type="text",
                ))

        # Image OCR chunks
        for img_idx, ocr_text in enumerate(ocr_texts):
            ocr_count += 1
            for idx, chunk in enumerate(
                _split_into_chunks(ocr_text, chunk_size, chunk_overlap)
            ):
                all_chunks.append(DocumentChunk(
                    text=f"[Image text, Page {page_no}]: {chunk}",
                    source_file=pdf_path.name,
                    page_number=page_no,
                    chunk_index=idx,
                    doc_hash=doc_hash,
                    chunk_type="image_ocr",
                    metadata={"image_index": img_idx},
                ))

    logger.info(
        "  → %d text pages, %d image OCR extractions, %d total chunks",
        text_count, ocr_count, len(all_chunks),
    )
    return all_chunks


def ocr_status() -> dict:
    available = _ocr_available()
    return {
        "available": available,
        "message":   (
            "✅ EasyOCR enabled — text will be extracted from images inside PDFs"
            if available else
            "⚠️ EasyOCR not installed — only text extracted (no image OCR)\n"
            "   Fix: pip install easyocr"
        ),
    }
