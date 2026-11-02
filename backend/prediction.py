import re, json, joblib
from .config import MODEL_PATH, VECTORIZER_PATH, INFO_PATH

_model = _vectorizer = None
_info = {}

def load_artifacts():
    global _model, _vectorizer, _info
    if _model is not None and _vectorizer is not None:
        return _model, _vectorizer
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        return None, None
    try:
        _model, _vectorizer = joblib.load(MODEL_PATH), joblib.load(VECTORIZER_PATH)
        if INFO_PATH.exists():
            _info = json.loads(INFO_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("Model load error:", exc)
        _model = _vectorizer = None
    return _model, _vectorizer

def model_info():
    load_artifacts()
    return dict(_info)

def clean_text(value):
    value = re.sub(r"https?://\S+|www\.\S+", " URL ", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()

def detect_language(text):
    devanagari = sum("\u0900" <= c <= "\u097f" for c in text)
    latin = sum(c.isascii() and c.isalpha() for c in text)
    return "Hindi/Devanagari" if devanagari > max(2, latin * .15) else "English or Latin-script"

def translate_if_needed(text, language):
    if language != "Hindi/Devanagari":
        return text, False, None
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        if translated:
            return translated, True, "Hindi text was translated to English; translation may change meaning."
    except Exception:
        pass
    return text, False, "Hindi detected, but translation was unavailable. An English-trained model may not reliably analyze this text."

def predict_text(text):
    model, vectorizer = load_artifacts()
    if model is None:
        raise RuntimeError("Model artifacts missing. Copy compatible files into backend/model or run: python -m backend.train_model")
    original = clean_text(text)
    language = detect_language(original)
    model_text, translated, warning = translate_if_needed(original, language)
    matrix = vectorizer.transform([model_text])
    raw = str(model.predict(matrix)[0]).strip().lower()
    prediction = "Likely Fake" if raw in {"fake","false","0","untrue"} else ("Likely Real" if raw in {"real","true","1","reliable"} else raw)
    confidence = None
    try:
        if hasattr(model, "predict_proba"):
            confidence = round(float(max(model.predict_proba(matrix)[0]) * 100), 2)
    except Exception:
        pass
    return {"prediction":prediction, "confidence":confidence, "language":language,
            "translated":translated, "warning":warning, "model_text":model_text, "matrix":matrix}
