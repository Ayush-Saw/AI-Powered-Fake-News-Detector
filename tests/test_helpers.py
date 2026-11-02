from backend.prediction import clean_text, detect_language
from backend.train_model import label_clean

def test_labels():
    assert label_clean("FAKE")=="fake"
    assert label_clean("real")=="real"
    assert label_clean("unknown") is None

def test_hindi_detection():
    assert detect_language("यह एक हिंदी समाचार है")=="Hindi/Devanagari"

def test_url_cleaning():
    assert "URL" in clean_text("Read https://example.com today")
