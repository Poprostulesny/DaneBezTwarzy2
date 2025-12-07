from anonymize import load_model, anonymize_text

# Załaduj model tylko raz (możesz zmienić ścieżkę jeśli trzeba)
MODEL_PATH = 'resources/model/final-model.pt'
_tagger = None

def get_tagger():
    global _tagger
    if _tagger is None:
        _tagger = load_model(MODEL_PATH)
    return _tagger

def get_anonymized_and_placeholder_text(text: str):
    tagger = get_tagger()
    anonymized, _ = anonymize_text(text, tagger)
    # Na razie oba identyczne, można rozdzielić w przyszłości
    return anonymized, anonymized
