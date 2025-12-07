from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anonymize import load_model, anonymize_text
from template_filler.filler import TagFiller

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
_filler = None

def get_tagger():
    global _tagger
    if _tagger is None:
        _tagger = load_model(MODEL_PATH)
    return _tagger

def get_filler():
    global _filler
    if _filler is None:
        _filler = TagFiller()
    return _filler

def get_anonymized_and_placeholder_text(text: str):
    tagger = get_tagger()
    filler = get_filler()
    
    # Anonimizacja - zamiana encji na tagi [NAME], [CITY] itd.
    anonymized, _, _ = anonymize_text(text, tagger)
    
    # Wypełnienie tagów losowymi wartościami z odmianą gramatyczną
    replaced = filler.fill(anonymized)
    
    return anonymized, replaced


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
