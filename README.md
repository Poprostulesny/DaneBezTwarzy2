# Dane bez twarzy — offline anonymization tool (Polish)

Projekt generuje syntetyczne dane NER dla języka polskiego, trenuje model NER (Flair + HerBERT),
oraz udostępnia prostą funkcję inferencyjną do anonimizacji tekstu.

## Etykiety NER (25 kategorii)

### Kategoria 1: Dane identyfikacyjne osobowe

- `{name}` – imiona
- `{surname}` – nazwiska
- `{age}` – wiek
- `{date-of-birth}` – data urodzenia
- `{date}` – inne daty wydarzeń pozwalające identyfikować osobę
- `{sex}` – płeć
- `{religion}` – wyznanie
- `{political-view}` – poglądy polityczne
- `{ethnicity}` – pochodzenie etniczne/narodowe
- `{sexual-orientation}` – orientacja seksualna
- `{health}` – dane o stanie zdrowia
- `{relative}` – relacje rodzinne ujawniające tożsamość

### Kategoria 2: Dane kontaktowe i lokalizacyjne

- `{city}` – miasto
- `{address}` – pełne dane adresowe
- `{email}` – adresy e-mail
- `{phone}` – numery telefonów

### Kategoria 3: Identyfikatory dokumentów i tożsamości

- `{pesel}` – numery PESEL
- `{document-number}` – numery dokumentów

### Kategoria 4: Dane zawodowe i edukacyjne

- `{company}` – nazwa pracodawcy
- `{school-name}` – nazwa szkoły
- `{job-title}` – stanowisko lub funkcja

### Kategoria 5: Informacje finansowe

- `{bank-account}` – numer rachunku bankowego
- `{credit-card-number}` – numery kart płatniczych

### Kategoria 6: Identyfikatory cyfrowe i loginy

- `{username}` – nazwy użytkowników, loginy
- `{secret}` – hasła, klucze API

---

## Instalacja

### Linux/macOS (bash)

```bash
# Utwórz i aktywuj środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Uwaga:** Instalacja `flair` może wymagać dopasowania wersji `torch` do Twojego GPU/CPU.

---

## Struktura projektu

```
DaneBezTwarzy2/
├── config.py              # Konfiguracja: etykiety, tagi anonimizacji
├── data_generator.py      # Generator syntetycznego korpusu NER
├── generate_values.py     # Generator rozbudowanych plików values.txt
├── train.py               # Skrypt treningowy (Flair + HerBERT)
├── anonymize.py           # 🔐 Główny skrypt do anonimizacji tekstu
├── inference.py           # Funkcja anonymize(text) - stary interfejs
├── utils.py               # Funkcje korupcji tekstu (leet-speak, typo)
├── convert_data.py        # Konwerter zdań z pliku Dane do mixed_templates.txt
├── mixed_templates.txt    # Szablony zdań z placeholderami
├── test_data.txt          # Przykładowe dane do testowania anonimizacji
├── requirements.txt       # Zależności Python
├── Dane                   # Surowe dane ze zdaniami
├── template_filler/       # 🔄 Moduł rekonstrukcji tekstu
│   ├── __init__.py        # Eksportuje TagFiller, PolishInflector
│   ├── __main__.py        # CLI: python -m template_filler
│   └── filler.py          # TagFiller + PolishInflector (Morfeusz2)
└── data/                  # Foldery z wartościami i szablonami per tag
    ├── name/
    │   ├── values.txt     # Lista imion
    │   └── templates.txt  # Szablony zdań z {name}
    ├── surname/
    ├── city/
    └── ...
```

---

## Jak generować dane treningowe

### 1. Konwersja surowych danych (opcjonalnie)

Jeśli masz plik `Dane` z nowymi zdaniami, uruchom:

```bash
python convert_data.py
```

Konwerter wyciągnie zdania i zapisze je do `mixed_templates.txt`.

### 2. Generowanie korpusu

```bash
# Szybki test (mały korpus)
python -c "from data_generator import generate_corpus; c=generate_corpus(n_per_template=5); print(f'train={len(c.train)}, dev={len(c.dev)}, test={len(c.test)}')"

# Pełna generacja
python data_generator.py
```

Generator:

- Wczytuje szablony z `mixed_templates.txt` i `data/*/templates.txt`
- Wczytuje wartości z `data/*/values.txt`
- Stosuje korupcję tekstu (leet-speak, literówki) z prawdopodobieństwem ~25%
- Tworzy korpus Flair z podziałem 80/10/10 (train/dev/test)

---

## Trening modelu

```bash
python train.py
```

Domyślne parametry:

- Model bazowy: `allegro/herbert-base-cased`
- Epoki: 6
- Batch size: 8
- Learning rate: 5e-5
- CRF: tak

Model zostanie zapisany w `resources/model/`.

### Parametry treningowe (opcjonalnie)

Edytuj `train.py` lub użyj w kodzie:

```python
from train import train_model
trainer = train_model(epochs=10, model_dir="my_model")
```

---

## Anonimizacja tekstu

### Skrypt `anonymize.py`

Główny skrypt do anonimizacji tekstu. Obsługuje różne tryby działania:

#### Anonimizacja tekstu z linii poleceń

```bash
python anonymize.py "Jan Kowalski mieszka w Warszawie"
```

#### Anonimizacja pliku

```bash
# Anonimizacja pliku (wynik zapisze do input_anonymized.txt)
python anonymize.py -i dane.txt

# Anonimizacja z podaniem pliku wyjściowego
python anonymize.py -i dane.txt -o anonimowe.txt

# Z wyświetlaniem szczegółów wykrytych encji
python anonymize.py -i dane.txt -o anonimowe.txt -v
```

#### Anonimizacja ze standardowego wejścia

```bash
echo "Mój PESEL to 90010112345" | python anonymize.py
```

#### Tryb interaktywny

```bash
python anonymize.py --interactive
```

#### Różne formaty wyjścia

```bash
# Format tekstowy (domyślny)
python anonymize.py "Jan Kowalski" --format text

# Format JSON (z encjami)
python anonymize.py "Jan Kowalski" --format json

# Format CSV
python anonymize.py "Jan Kowalski" --format csv
```

#### Użycie własnego modelu

```bash
python anonymize.py -m models/custom/best-model.pt "Tekst do anonimizacji"
```

### Przykładowy wynik

Wejście (`test_data.txt`):

```
Nazywam się Jan Kowalski i mieszkam w Warszawie przy ul. Marszałkowskiej 15/3.
Mój numer PESEL to 90010112345, a numer telefonu to +48 500 123 456.
```

Wyjście:

```
Nazywam się [IMIĘ] [NAZWISKO] i mieszkam w [MIASTO] przy [ADRES].
Mój numer PESEL to [PESEL], a numer telefonu to [TELEFON].
```

---

## Rekonstrukcja tekstu (wypełnianie tagów)

Moduł `template_filler` pozwala na odwrócenie procesu anonimizacji - zamienia tagi `[IMIĘ]`, `[MIASTO]` itd. na losowe, ale **gramatycznie poprawne** wartości.

### Jak działa

```
Tekst oryginalny: "Jan Kowalski mieszka w Warszawie."
        ↓
Model NER (anonymize.py): wykrywa i taguje dane wrażliwe
        ↓
Tekst zanonimizowany: "Pani [IMIĘ] [NAZWISKO] mieszka w [MIASTO]."
        ↓
TagFiller (template_filler): wypełnia tagi losowymi wartościami z odmianą
        ↓
Tekst zrekonstruowany: "Pani Anna Kowalska mieszka w Krakowie."
```

### Użycie

```bash
# Z linii poleceń
python -m template_filler "Pani [IMIĘ] [NAZWISKO] mieszka w [MIASTO]."

# Z pliku
python -m template_filler -i anonimized.txt -o filled.txt

# W kodzie Python
from template_filler import TagFiller
filler = TagFiller()
result = filler.fill("Spotkałem się z [IMIĘ] w [MIASTO].")
# → "Spotkałem się z Piotrem w Krakowie."
```

### Architektura

System składa się z dwóch komponentów:

1. **TagFiller** - główna klasa wypełniająca tagi:

   - Losowy wybór wartości z `data/{tag}/values.txt`
   - Analiza kontekstu (przyimki, czasowniki) do określenia przypadka
   - Wywołanie Morfeusz2 do odmiany

2. **PolishInflector** - wrapper na Morfeusz2:
   - Generuje formy odmienione polskich słów
   - Cache dla wydajności
   - Obsługuje frazy wielowyrazowe ("Zielona Góra" → "Zielonej Górze")

### Wykrywanie przypadka gramatycznego

System automatycznie wykrywa wymagany przypadek na podstawie:

| Kontekst                    | Przypadek         | Przykład                |
| --------------------------- | ----------------- | ----------------------- |
| w, we, na, przy             | miejscownik (loc) | "w Krakowie"            |
| do, od, z, bez, dla         | dopełniacz (gen)  | "do Warszawy"           |
| przez                       | biernik (acc)     | "przez Kraków"          |
| z + czasownik ruchu         | dopełniacz        | "z Krakowa przyjechał"  |
| z + czasownik towarzyszenia | narzędnik         | "spotkałem się z Janem" |
| Pani, Pana                  | dopełniacz        | "Pani Anny"             |

### Wydajność

| Metoda                          | Zdań/sekundę | Opis                                         |
| ------------------------------- | ------------ | -------------------------------------------- |
| **TagFiller (Morfeusz2)**       | ~19 000      | ✅ Szybkie, regułowe                         |
| HerBERT MLM (pseudo-perplexity) | ~0.5         | ❌ Wolne, każdy kandydat wymaga forward pass |

### Dlaczego nie używamy modelu NER do predykcji wartości?

1. **Model NER wykrywa, nie generuje**: Nasz wytrenowany model (`final-model.pt`) to **sekwencyjny tagger** - wykrywa gdzie są dane wrażliwe i jaką mają kategorię. Nie jest w stanie generować nowych wartości.

2. **Tokeny ≠ słowa**: Model operuje na subtokenach (BPE). "Warszawa" może być rozbita na `["War", "##szaw", "##a"]`. Predykcja subtokena nie da nam sensownego słowa.

3. **Brak mechanizmu generacji**: NER to klasyfikacja tokena (B-NAME, I-NAME, O), nie generacja tekstu. Potrzebowalibyśmy modelu generatywnego (GPT-like) lub MLM do uzupełniania.

4. **Odmiana gramatyczna**: Nawet gdybyśmy wybrali "Warszawa", musimy ją odmienić do "Warszawie" (miejscownik). To wymaga analizy morfologicznej (Morfeusz2), nie ML.

### Dlaczego HerBERT MLM jest wolny?

Podejście z pseudo-perplexity wymaga:

- Dla każdego kandydata (np. 20 imion)
- Dla każdej formy odmiany (7 przypadków)
- Dla każdego tokena w zdaniu (~15)
- **Forward pass przez cały model** (110M parametrów)

To daje: 20 × 7 × 15 = **2100 forward passów na jedno zdanie!**

Nasze rozwiązanie z Morfeusz2 jest **~40 000x szybsze** bo:

- Losowy wybór = O(1)
- Odmiana = lookup w słowniku morfologicznym

### Ograniczenia

1. **Obce imiona**: Morfeusz2 nie zna wszystkich imion obcych (np. "Yaroslav", "Serhii"). Takie imiona nie są odmieniane.

2. **Nazwy własne firm**: Niektóre nazwy firm mogą być niepoprawnie odmieniane.

3. **Kontekst semantyczny**: System nie rozumie semantyki - może podstawić męskie imię po "Pani" (choć gramatycznie odmieni poprawnie).

---

## Inferencja (stary interfejs)

```bash
python -c "from inference import anonymize; print(anonymize('Nazywam się Anna Nowak i mieszkam w Krakowie.'))"
```

Przykładowy wynik:

```
Nazywam się {name} {surname} i mieszkam w {city} .
```

### W kodzie Python:

```python
from inference import anonymize

text = "Jan Kowalski, lat 35, zamieszkały przy ul. Marszałkowskiej 10 w Warszawie."
anonymized = anonymize(text)
print(anonymized)
# Jan Kowalski → {name} {surname}
# 35 → {age}
# ul. Marszałkowskiej 10 → {address}
# Warszawie → {city}
```

---

## Korupcja tekstu (data augmentation)

Funkcja `corrupt_text()` w `utils.py` wprowadza realistyczne zniekształcenia:

- **Leet-speak:** `a→@`, `o→0`, `k→|<`, `e→3`, `s→$`
- **Literówki OCR:** `m→rn`, `l→1`, `n→m`
- **Polskie znaki:** `ó→o`, `ł→l`
- **Losowe pominięcia i duplikacje**

Przykład:

```python
from utils import corrupt_text
print(corrupt_text("Kowalski", prob=0.4))
# Możliwy wynik: "|<0vv@l$|<i"
```

---

## Dodawanie własnych danych

### 1. Dodaj wartości

Utwórz/edytuj plik `data/{tag}/values.txt`:

```
# data/name/values.txt
Jan
Maria
Piotr
...
```

### 2. Dodaj szablony

Utwórz/edytuj plik `data/{tag}/templates.txt`:

```
# data/name/templates.txt
Moje imię to {name}.
Pan {name} jest kierownikiem projektu.
```

### 3. Lub dodaj do mixed_templates.txt

Szablony mogą zawierać wiele różnych tagów:

```
{name} {surname} mieszka w {city} i pracuje jako {job-title}.
```

---

## Wymagania systemowe

- Python 3.8+
- PyTorch (CPU lub CUDA)
- ~4GB RAM dla treningu (więcej dla większych korpusów)
- ~2GB na model HerBERT

---

## Pliki projektu

| Plik                | Opis                                         |
| ------------------- | -------------------------------------------- |
| `config.py`         | Konfiguracja, etykiety, przykładowe szablony |
| `utils.py`          | Funkcje korupcji tekstu                      |
| `data_generator.py` | Generacja syntetycznego korpusu Flair        |
| `train.py`          | Skrypt treningowy (Flair + HerBERT)          |
| `inference.py`      | Funkcja `anonymize(text)`                    |
| `convert_data.py`   | Konwerter pliku Dane do mixed_templates.txt  |
| `requirements.txt`  | Lista zależności                             |

---

## Licencja

Projekt przygotowany do hackathonu. Użycie zgodne z licencjami modelu HerBERT i biblioteki Flair.

---

## Autor

Senior ML Engineer (NLP)


# FRONTEND
cd anonymizer-ui && npm install && npm run dev