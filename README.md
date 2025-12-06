# Dane bez twarzy — offline anonymization tool (Polish)

Projekt generuje syntetyczne dane NER dla języka polskiego, trenuje model NER (Flair + HerBERT),
oraz udostępnia prostą funkcję inferencyjną do anonimizacji tekstu.

Instrukcja instalacji (PowerShell, Windows):

1. Utwórz i aktywuj środowisko wirtualne (opcjonalne, lecz zalecane):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Zainstaluj zależności:

```powershell
pip install -r requirements.txt
```

Uwaga: instalacja `flair` może wymagać dopasowania wersji `torch` do Twojego GPU/CPU.

Jak generować dane:

- Edytuj `config.TEMPLATES` i wstaw swoje szablony w formacie z placeholderami, np.:

```
"Moje imię to {name} i mieszkam w {city}."
```

- Uruchom prosty generator (zwraca Corpus w konsoli):

```powershell
python -c "import data_generator as dg; c=dg.generate_corpus(n_per_template=100); print(len(c.train))"
```

Jak trenować model:

```powershell
python train.py
```

Domyślnie `train.py` wygeneruje syntetyczny korpus (jeśli nie dostarczysz własnego) i rozpocznie trening.
Model zostanie zapisany w `resources/model`.

Jak używać inferencji (anonimizacja):

```powershell
python -c "from inference import anonymize; print(anonymize('Nazywam się Anna Nowak i mieszkam w Kraków.'))"
```

Pliki projektu:
- `config.py` — konfiguracja, etykiety, przykładowe `TEMPLATES`.
- `utils.py` — funkcje do wprowadzania szumów (leet, błędy OCR itp.).
- `data_generator.py` — generacja syntetycznego korpusu Flair.
- `train.py` — skrypt treningowy (Flair + Transformer embeddingi).
- `inference.py` — funkcja `anonymize(text)` zwracająca tekst z tagami.
- `requirements.txt` — lista zależności.

Uwagi i dalsze kroki:
- Szablony należy dopracować, aby dobrze odzwierciedlały rzeczywiste dane.
- Możesz rozszerzyć `utils.corrupt_text` o dodatkowe typy szumów (OCR, zamiana liter diakrytycznych itp.).
- Po uzyskaniu prawdziwych danych oznakowanych (gdy będą dostępne) warto dopracować trening i walidację.

Autor: Senior ML Engineer (NLP) — projekt przygotowany do hackathonu.
