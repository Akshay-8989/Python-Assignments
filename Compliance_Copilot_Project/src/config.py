"""
config.py  –  Central configuration for the Compliance Copilot v3.
"""
import os
from pathlib import Path

# ── Block ALL HuggingFace network calls ──────────────────────────────────────
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"
os.environ["HF_HUB_OFFLINE"]       = "1"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent
UPLOAD_DIR      = Path(os.getenv("UPLOAD_PATH",      str(BASE_DIR / "data" / "uploads")))
VECTORSTORE_DIR = Path(os.getenv("VECTORSTORE_PATH", str(BASE_DIR / "data" / "vectorstore")))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# ── Phi-2 Local Path ──────────────────────────────────────────────────────────
# !! SET THIS TO YOUR LOCAL PHI-2 FOLDER !!
# Example:  r"D:\phi-2"   or   r"C:\Users\Akshay\models\phi-2"
PHI2_MODEL_NAME = os.getenv("PHI2_MODEL_NAME", r"D:\phi-2")

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "6"))

# ── Generation ────────────────────────────────────────────────────────────────
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "800"))
TEMPERATURE    = float(os.getenv("TEMPERATURE",  "0.1"))

# ── EasyOCR ───────────────────────────────────────────────────────────────────
# Languages for EasyOCR. 'en' = English. Add more if needed e.g. ['en', 'hi']
# Models are downloaded once on first use (~100 MB) and cached locally.
EASYOCR_LANGUAGES = ["en"]

# ── UI ────────────────────────────────────────────────────────────────────────
APP_TITLE = os.getenv("APP_TITLE", "Banking Policy & Compliance Copilot")
