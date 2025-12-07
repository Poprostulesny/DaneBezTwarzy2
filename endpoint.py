from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anonymize import load_model, anonymize_text

app = FastAPI(title="NoFace Anonymizer API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class AnonymizeRequest(BaseModel):
    text: str


class AnonymizeResponse(BaseModel):
    anonymizedText: str
    replacedText: str


@app.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize(request: AnonymizeRequest):
    anonymized, replaced = get_anonymized_and_placeholder_text(request.text)
    return AnonymizeResponse(
        anonymizedText=anonymized,
        replacedText=replaced
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
