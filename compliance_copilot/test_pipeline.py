"""
test_pipeline.py  –  Run this to diagnose any issues before using the UI.
Usage:  python test_pipeline.py
"""
import sys, os
sys.path.insert(0, '.')

print("=" * 60)
print("STEP 1: Vector Store retrieval test")
print("=" * 60)
try:
    from src.vector_store import ComplianceVectorStore
    from pathlib import Path

    store = ComplianceVectorStore(Path('data/vectorstore'))
    count = store.document_count()
    print(f"Chunks in store: {count}")

    if count == 0:
        print("WARNING: Store is empty. Upload a PDF first via the UI.")
    else:
        results = store.similarity_search('What documents are required for KYC?', k=3)
        print(f"Search results: {len(results)}")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  Score : {score:.3f}")
            print(f"  Page  : {doc.metadata.get('page','?')}")
            print(f"  Text  : {doc.page_content[:150]}")
        print("\n✅ Vector store: OK")
except Exception as e:
    import traceback
    print(f"❌ Vector store ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("STEP 2: Phi-2 LLM test")
print("=" * 60)
try:
    from src.config import PHI2_MODEL_NAME
    print(f"Phi-2 path: {PHI2_MODEL_NAME}")

    if not PHI2_MODEL_NAME or PHI2_MODEL_NAME == r"D:\phi-2":
        print("⚠️  WARNING: PHI2_MODEL_NAME is still the default placeholder.")
        print("   Open src/config.py and set it to your actual Phi-2 folder path.")
    else:
        from src.llm_engine import get_llm
        print("Loading model... (may take 1-2 minutes on first run)")
        llm = get_llm(model_name=PHI2_MODEL_NAME)
        print("Model loaded: OK")
        result = llm.generate(
            "Instruct: What is KYC in banking? Give a one sentence answer. Output:"
        )
        print(f"Test output: {result}")
        print("✅ Phi-2 LLM: OK")
except Exception as e:
    import traceback
    print(f"❌ Phi-2 ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("STEP 3: Full RAG pipeline test")
print("=" * 60)
try:
    from src.rag_pipeline import ComplianceRAGPipeline
    pipeline = ComplianceRAGPipeline()

    if pipeline.vectorstore.document_count() == 0:
        print("Skipping — no documents indexed. Upload a PDF first.")
    else:
        print("Running query...")
        response = pipeline.query("What documents are required for KYC?")
        print(f"Answer  : {response.answer[:300]}")
        print(f"Sources : {len(response.sources)}")
        if response.error:
            print(f"Error   : {response.error}")
        print("\n✅ RAG pipeline: OK")
except Exception as e:
    import traceback
    print(f"❌ RAG pipeline ERROR: {e}")
    traceback.print_exc()
