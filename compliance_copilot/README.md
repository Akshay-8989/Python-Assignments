# 🏦 GenAI Banking Policy & Compliance Copilot v3

RAG chatbot for banking policy PDFs — fully local, fully offline after setup.

**Stack:** Phi-2 (local SLM) · FAISS (vector DB) · EasyOCR (image extraction) · TF-IDF+SVD (embeddings)

---

## 🆕 What's new in v3

| Feature | v1 | v3 |
|---|---|---|
| Vector DB | TF-IDF pickle | **FAISS IndexFlatIP** |
| Embeddings | TF-IDF sparse | **TF-IDF + SVD 256-dim dense** |
| Image extraction | ❌ None | ✅ **EasyOCR** (pip install only) |
| External apps needed | None | **None** — everything is pip |

---

## ⚙️ Setup

### 1. Set your Phi-2 path
Open `src/config.py` and update:
```python
PHI2_MODEL_NAME = r"D:\phi-2"   # ← your actual local folder path
```

### 2. Install all dependencies (one command)
```bash
pip install -r requirements.txt
```

This installs everything including EasyOCR and FAISS.
No Tesseract, no external apps — everything is pure Python/pip.

### 3. First run note
EasyOCR downloads its recognition model (~100 MB) on first use.
After that it works fully offline.

### 4. Run
```bash
streamlit run app.py
```

---

## 🚀 How to use

1. Open `http://localhost:8501`
2. Check the OCR status in the sidebar:
   - 🟢 Green = EasyOCR active, images inside PDFs will be read
   - 🟡 Yellow = EasyOCR not installed, run `pip install easyocr`
3. Upload your policy PDFs — you'll see:
   - `X chunks` = text only PDFs
   - `X chunks (Y text + Z image OCR)` = PDFs with embedded images
4. Type any question and press **Enter**
5. Answers appear with sources — 📄 text or 🖼️ image sources

---

## 🔧 Troubleshoot

```bash
python test_pipeline.py    # run full diagnostic
```

| Problem | Fix |
|---|---|
| `faiss not found` | `pip install faiss-cpu` |
| `easyocr not found` | `pip install easyocr` |
| Still hitting HuggingFace | Set `PHI2_MODEL_NAME` to your local path in `src/config.py` |
| Old index errors | Delete `data/vectorstore/` contents and re-upload PDFs |
| Empty answers | Check Phi-2 path, run `python test_pipeline.py` |

---

## 📁 Project Structure

```
compliance_copilot/
├── app.py                    ← Streamlit UI — run this
├── test_pipeline.py          ← Diagnostic script
├── requirements.txt          ← pip install -r requirements.txt
│
├── src/
│   ├── config.py             ← Set PHI2_MODEL_NAME here
│   ├── document_processor.py ← PDF text + EasyOCR image extraction
│   ├── vector_store.py       ← FAISS + TF-IDF/SVD embeddings
│   ├── llm_engine.py         ← Phi-2 local inference
│   └── rag_pipeline.py       ← Full RAG orchestration
│
└── data/
    ├── uploads/              ← PDFs saved here
    └── vectorstore/          ← FAISS index saved here
        ├── faiss_index.bin
        ├── faiss_meta.pkl
        ├── tfidf_vectorizer.pkl
        └── svd_transformer.pkl
```
