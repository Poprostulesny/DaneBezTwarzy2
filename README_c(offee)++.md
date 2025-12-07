# DaneBezTwarzy — Anonimizacja danych osobowych (Polish NER)

**Zespół: C(offe)++3**

## O projekcie

Narzędzie do automatycznej anonimizacji danych osobowych w tekstach polskich.

**Podejście:** Fine-tuned HerBERT NER (Named Entity Recognition) — model językowy HerBERT (`allegro/herbert-base-cased`) dotrenowany na zadaniu rozpoznawania 25 kategorii encji osobowych.

**Kluczowe cechy:**

- 🎯 25 kategorii danych wrażliwych (PESEL, imiona, adresy, numery kart, etc.)
- 🚀 Wydajność: ~27,400 znaków/sekundę na GPU
- 🇵🇱 Dedykowany dla języka polskiego
- 🔄 Moduł rekonstrukcji z odmianą gramatyczną (Morfeusz2)

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

### 2. Trening modelu

```bash
# Wygeneruj dane treningowe
python data_generator.py

# Wytrenuj model
python train.py

Po 30 minutach trenowania osiąga:
F-score (micro) 0.9813
F-score (macro) 0.9826
Accuracy 0.9689
```

**Trenowane Na Systemie:**

- Python 3.8+
- ~32GB - RAM (trening)
- RTX 3090 - GPU (CUDA)

Model zostanie zapisany w `resources/model/final-model.pt`.

### 3. Anonimizacja tekstu

```bash
# Pojedynczy tekst
python anonymize.py "Jan Kowalski z Warszawy, tel. 500123456"

# Plik tekstowy
python anonymize.py -i dane.txt -o anonimowe.txt
```

**Przykład wyniku:**

```
Wejście:  Jan Kowalski mieszka w Warszawie, tel. 500123456
Wyjście:  [name] [surname] mieszka w [city], tel. [phone]
```

### 4. Rekonstrukcja tekstu (wypełnianie tagów)

Po anonimizacji możesz wypełnić tagi losowymi, gramatycznie poprawnymi wartościami:

```bash
# Pojedynczy tekst
python -m template_filler "Pani [name] [surname] mieszka w [city]."

# Plik tekstowy
python -m template_filler -i anonimowe.txt -o zrekonstruowane.txt
```

**Przykład wyniku:**

```
Wejście:  [name] [surname] mieszka w [city], tel. [phone]
Wyjście:  Andrzej Nowak mieszka w Krakowie, tel. 132546987
```

## Kategorie danych (25 etykiet NER)

| Kategoria          | Etykiety                                                                  |
| ------------------ | ------------------------------------------------------------------------- |
| **Dane osobowe**   | NAME, SURNAME, AGE, DATE-OF-BIRTH, DATE, SEX                              |
| **Dane wrażliwe**  | RELIGION, POLITICAL-VIEW, ETHNICITY, SEXUAL-ORIENTATION, HEALTH, RELATIVE |
| **Lokalizacja**    | CITY, ADDRESS                                                             |
| **Kontakt**        | EMAIL, PHONE                                                              |
| **Dokumenty**      | PESEL, DOCUMENT-NUMBER                                                    |
| **Praca/Edukacja** | COMPANY, SCHOOL-NAME, JOB-TITLE                                           |
| **Finanse**        | BANK-ACCOUNT, CREDIT-CARD-NUMBER                                          |
| **Cyfrowe**        | USERNAME, SECRET                                                          |

---

## Struktura projektu (mapa repozytorium)

```
DaneBezTwarzy2/
│
├── 📄 README.md                    # Ten plik - dokumentacja projektu
├── 📄 output_coffe_3.txt           # Zanonimizowany plik wynikowy
├── 📄 performance_coffe_3.txt      # Metryki wydajności i sprzęt
├── 📄 preprocessing_coffe_3.md     # Opis preprocessingu danych
├── 📄 synthetic_generation_coffe_3.md  # Opis generacji syntetycznej
│
├── 🔧 anonymize.py           # GŁÓWNY SKRYPT - anonimizacja tekstu
├── 🔧 train.py               # Trening modelu NER
├── 🔧 data_generator.py      # Generator danych treningowych
├── 🔧 inference.py           # API do anonimizacji
├── 🔧 config.py              # Konfiguracja 25 etykiet NER
├── 🔧 utils.py               # Funkcje pomocnicze (korupcja tekstu)
├── 🔧 generate_values.py     # Rozszerzanie słowników wartości
├── 🔧 convert_data.py        # Konwersja surowych danych
├── 📋 requirements.txt       # Zależności Python
│
├── 📁 template_filler/       # Moduł rekonstrukcji tekstu
│   ├── filler.py             # TagFiller + PolishInflector (Morfeusz2)
│   └── __main__.py           # CLI
│
├── 📁 data/                  # Słowniki wartości i szablony
│   ├── name/values.txt       # ~200 polskich imion
│   ├── surname/values.txt    # ~300 polskich nazwisk
│   ├── city/values.txt       # ~100 miast Polski
│   └── ...                   # Pozostałe 22 kategorie
│
└── 📁 resources/model/       # Wytrenowany model
    └── final-model.pt        # Wagi modelu (~500MB)
```

---

## Szczegóły techniczne

### Model NER

- **Architektura:** Flair SequenceTagger + HerBERT (allegro/herbert-base-cased)
- **Warstwa wyjściowa:** CRF (Conditional Random Field)
- **Embeddingi:** Transformer embeddings z HerBERT

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

| Kontekst        | Przypadek   | Przykład       |
| --------------- | ----------- | -------------- |
| w, we, na, przy | miejscownik | "w Krakowie"   |
| do, od, z, bez  | dopełniacz  | "do Warszawy"  |
| przez           | biernik     | "przez Kraków" |
| spotkałem się z | narzędnik   | "z Janem"      |
| Pani, Pana      | dopełniacz  | "Pani Anny"    |

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
# → "[name] [surname], tel. [phone], mieszka w [city]."
```

### Rekonstrukcja

```python
from template_filler.filler import TagFiller

filler = TagFiller()
result = filler.fill("Spotkałem się z [name] w [city].")
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

Edytuj pliki w data/[kategoria]/values.txt:

```
# data/name/values.txt
Jan
Anna
Piotr
...
```

### Dodawanie szablonów

Edytuj data/[kategoria]/templates.txt lub data/mixed_templates.txt:

```
[name] [surname] pracuje jako [job-title] w [company].
Mój PESEL to [pesel], a numer telefonu [phone].
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
