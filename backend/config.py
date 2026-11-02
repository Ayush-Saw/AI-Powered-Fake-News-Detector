from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
DATASET = BACKEND / "dataset" / "fake_news.csv"
MODEL_DIR = BACKEND / "model"
MODEL_PATH = MODEL_DIR / "fake_news_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
INFO_PATH = MODEL_DIR / "model_info.json"
DB_PATH = BACKEND / "fake_news.db"
MAX_TEXT_CHARS = 20000
