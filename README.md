# DaneBezTwarzy — Anonimizacja danych osobowych (Polish NER)

Narzędzie do automatycznej anonimizacji danych osobowych w tekstach polskich. Wykorzystuje model NER (Named Entity Recognition) oparty na HerBERT do wykrywania 25 kategorii danych wrażliwych.

---

## Szybki start

### 1. Instalacja

```bash
# Sklonuj repozytorium
git clone https://github.com/Poprostulesny/DaneBezTwarzy2.git
cd DaneBezTwarzy2

# Utwórz środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# lub: .\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Zainstaluj zależności
pip install -r requirements.txt
```

**Wymagania systemowe:**
- Python 3.8+
- ~4GB RAM (trening), ~2GB RAM (inferencja)
- GPU opcjonalne (CUDA) - przyspiesza trening ~10x

### 2. Trening modelu

```bash
# Wygeneruj dane treningowe
python data_generator.py

# Wytrenuj model (domyślnie 6 epok)
python train.py
```

Model zostanie zapisany w `resources/model/final-model.pt`.

### 3. Anonimizacja tekstu

```bash
# Pojedynczy tekst
python anonymize.py "Jan Kowalski mieszka w Warszawie, tel. 500123456"

# Plik tekstowy
python anonymize.py -i dane.txt -o anonimowe.txt

# Tryb interaktywny
python anonymize.py --interactive
```

**Przykład wyniku:**
```
Wejście:  Jan Kowalski mieszka w Warszawie, tel. 500123456
Wyjście:  [NAME] [SURNAME] mieszka w [CITY], tel. [PHONE]
```

### 4. Rekonstrukcja tekstu (wypełnianie tagów)

Po anonimizacji możesz wypełnić tagi losowymi, gramatycznie poprawnymi wartościami:

```bash
python -m template_filler.filler "Pani [NAME] [SURNAME] mieszka w [CITY]."
# → Pani Anna Kowalska mieszka w Krakowie.
```

System automatycznie:
- Wykrywa płeć z kontekstu ("Pani" → imię żeńskie)
- Dopasowuje nazwisko do płci (Kowalska, nie Kowalski)
- Odmienia przez przypadki ("w Krakowie", nie "w Kraków")
- Zachowuje spójność danych osobowych (PESEL zawiera datę urodzenia i płeć)

---

## Kategorie danych (25 etykiet NER)

| Kategoria | Etykiety |
|-----------|----------|
| **Dane osobowe** | NAME, SURNAME, AGE, DATE-OF-BIRTH, DATE, SEX |
| **Dane wrażliwe** | RELIGION, POLITICAL-VIEW, ETHNICITY, SEXUAL-ORIENTATION, HEALTH, RELATIVE |
| **Lokalizacja** | CITY, ADDRESS |
| **Kontakt** | EMAIL, PHONE |
| **Dokumenty** | PESEL, DOCUMENT-NUMBER |
| **Praca/Edukacja** | COMPANY, SCHOOL-NAME, JOB-TITLE |
| **Finanse** | BANK-ACCOUNT, CREDIT-CARD-NUMBER |
| **Cyfrowe** | USERNAME, SECRET |

---

## Struktura projektu

```
DaneBezTwarzy2/
├── anonymize.py           # Główny skrypt anonimizacji
├── train.py               # Trening modelu NER
├── data_generator.py      # Generator danych treningowych
├── inference.py           # API do anonimizacji
├── config.py              # Konfiguracja etykiet
├── utils.py               # Funkcje pomocnicze (korupcja tekstu)
├── generate_values.py     # Rozszerzanie słowników wartości
├── convert_data.py        # Konwersja surowych danych
├── requirements.txt       # Zależności Python
│
├── template_filler/       # Moduł rekonstrukcji tekstu
│   ├── filler.py          # TagFiller + PolishInflector + PersonContext
│   └── __main__.py        # CLI
│
├── data/                  # Słowniki wartości i szablony
│   ├── name/values.txt    # Lista imion
│   ├── surname/values.txt # Lista nazwisk
│   ├── city/values.txt    # Lista miast
│   └── ...                # Pozostałe kategorie
│
└── resources/model/       # Wytrenowany model
    └── final-model.pt
```

---

## Szczegóły techniczne

### Model NER

- **Architektura:** Flair SequenceTagger + HerBERT (allegro/herbert-base-cased)
- **Warstwa wyjściowa:** CRF (Conditional Random Field)
- **Embeddingi:** Transformer embeddings z HerBERT

### Parametry treningu (domyślne)

| Parametr | Wartość |
|----------|---------|
| Epoki | 6 |
| Batch size | 8 |
| Learning rate | 5e-5 |
| Scheduler | OneCycleLR |
| Model bazowy | allegro/herbert-base-cased |

### Dane treningowe

Generator (data_generator.py) tworzy syntetyczny korpus:
- Wczytuje szablony zdań z data/*/templates.txt i data/mixed_templates.txt
- Wypełnia placeholdery wartościami z data/*/values.txt
- Stosuje augmentację (literówki, leet-speak) ~25% przypadków
- Podział: 80% train / 10% dev / 10% test

---

## Moduł rekonstrukcji (template_filler)

Zamienia tagi anonimizacji na losowe wartości z **poprawną odmianą gramatyczną** i **spójnym kontekstem osobowym**.

### Jak działa

1. **Wykrywanie płci** z kontekstu (Pan/Pani, czasowniki: -łam/-łem)
2. **PersonContext** - spójna tożsamość osoby (imię, nazwisko, PESEL, wiek, data urodzenia)
3. **Losowy wybór** wartości zgodnych z płcią
4. **Odmiana** przez Morfeusz2 w odpowiedni przypadek gramatyczny

### Spójny kontekst osobowy

Tagi osobowe (`[NAME]`, `[SURNAME]`, `[AGE]`, `[DATE-OF-BIRTH]`, `[PESEL]`, `[SEX]`) są ze sobą powiązane:

```
Wejście:  Pani [NAME] [SURNAME], ur. [DATE-OF-BIRTH], PESEL: [PESEL], wiek: [AGE] lat.
Wyjście:  Pani Anna Kowalska, ur. 15.03.1985, PESEL: 85031512348, wiek: 39 lat.
```

- **Imię i nazwisko** pasują do wykrytej płci (Anna, Kowalska = żeńskie)
- **Data urodzenia** jest spójna z wiekiem (2025 - 1985 = 39 lat)
- **PESEL** zawiera datę urodzenia (850315) i cyfrę płci (8 = parzysta = kobieta)

### Wykrywanie płci

| Wskaźnik | Płeć | Przykład |
|----------|------|----------|
| Pani, panna, ona, jej | Żeńska | "Pani [NAME]" → Anna |
| Pan, on, jego | Męska | "Pan [NAME]" → Jan |
| Czasownik -łam, -ła | Żeńska | "zadzwoniłam do [NAME]" |
| Czasownik -łem, -ł | Męska | "rozmawiałem z [NAME]" |

### Wykrywanie przypadka gramatycznego

| Kontekst | Przypadek | Przykład |
|----------|-----------|----------|
| w, we, na, przy | miejscownik | "w Krakowie" |
| do, od, z, bez | dopełniacz | "do Warszawy" |
| przez | biernik | "przez Kraków" |
| spotkałem się z | narzędnik | "z Janem" |
| Pani, Pana | dopełniacz | "Pani Anny" |

### Wydajność

~19 000 zdań/sekundę (bez GPU, czyste reguły + Morfeusz2)

### Ograniczenia

- Obce imiona (np. "Yaroslav") nie są odmieniane (brak w słowniku Morfeusz2)
- Niektóre męskie imiona kończące się na -a (Kuba, Mykola) mogą być błędnie klasyfikowane jako żeńskie

---

## API Python

### Anonimizacja

```python
from inference import anonymize

text = "Jan Kowalski, tel. 500123456, mieszka w Warszawie."
result = anonymize(text)
print(result)
# → "{name} {surname}, tel. {phone}, mieszka w {city}."
```

### Rekonstrukcja

```python
from template_filler.filler import TagFiller

filler = TagFiller()

# Podstawowe użycie z odmianą
result = filler.fill("Spotkałem się z [NAME] w [CITY].")
print(result)
# → "Spotkałem się z Piotrem w Krakowie."

# Spójny kontekst osobowy
result = filler.fill("Pani [NAME] [SURNAME], PESEL: [PESEL], wiek: [AGE] lat.")
print(result)
# → "Pani Anna Kowalska, PESEL: 85031512348, wiek: 39 lat."
# (wszystkie dane są ze sobą spójne!)
```

---

## Rozszerzanie danych

### Dodawanie nowych wartości

Edytuj pliki w data/{kategoria}/values.txt:

```
# data/name/values.txt
Jan
Anna
Piotr
...
```

### Dodawanie szablonów

Edytuj data/{kategoria}/templates.txt lub data/mixed_templates.txt:

```
{name} {surname} pracuje jako {job-title} w {company}.
Mój PESEL to {pesel}, a numer telefonu {phone}.
```

### Generowanie rozszerzonych słowników

```bash
python generate_values.py
```

Używa biblioteki Faker do wygenerowania polskich imion, nazwisk, miast itp.

---

## Augmentacja danych (korupcja tekstu)

Funkcja corrupt_text() w utils.py wprowadza realistyczne zniekształcenia:

- **Leet-speak:** a→@, e→3, s→$
- **OCR błędy:** m→rn, l→1
- **Polskie znaki:** ó→o, ł→l

```python
from utils import corrupt_text
print(corrupt_text("Kowalski", prob=0.4))
# → "|<0w@l$ki"
```

---

## Dlaczego nie używamy ML do wypełniania tagów?

1. **Model NER wykrywa, nie generuje** - to sekwencyjny tagger (B-NAME, I-NAME, O), nie generator tekstu

2. **Tokeny ≠ słowa** - HerBERT operuje na subtokenach BPE. "Warszawa" → ["War", "##szaw", "##a"]

3. **Wydajność** - HerBERT MLM z pseudo-perplexity: ~0.5 zdań/s vs Morfeusz2: ~19000 zdań/s

4. **Odmiana gramatyczna** - wymaga analizy morfologicznej, nie ML

---

## Wymagania

```
flair>=0.12
transformers>=4.0.0
torch>=1.10
faker>=13.3.4
morfeusz2>=1.99
seqeval
sacremoses
```

---

## Licencja

Projekt hackathonowy. Użycie zgodne z licencjami HerBERT i Flair.

---

## Autor

Karol — Senior ML Engineer (NLP)
