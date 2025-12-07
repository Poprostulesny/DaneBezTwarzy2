# Preprocessing - C(offe)++3

## Źródła danych

### 1. Słowniki wartości (`data/*/values.txt`)

Dla każdej z 25 kategorii NER przygotowaliśmy słowniki zawierające przykładowe wartości:

| Kategoria            | Źródło danych                                       | Liczba przykładów |
| -------------------- | --------------------------------------------------- | ----------------- |
| `name`               | Popularne polskie imiona                            | ~200              |
| `surname`            | Popularne polskie nazwiska                          | ~300              |
| `city`               | Miasta w Polsce                                     | ~100              |
| `pesel`              | Generowane algorytmicznie (poprawna suma kontrolna) | dynamicznie       |
| `phone`              | Wzorce polskich numerów                             | ~50 wzorców       |
| `email`              | Generowane z imion/nazwisk + domeny                 | dynamicznie       |
| `bank-account`       | Wzorce IBAN PL                                      | dynamicznie       |
| `credit-card-number` | Wzorce kart (Visa, Mastercard)                      | dynamicznie       |
| ...                  | ...                                                 | ...               |

### 2. Szablony zdań (`data/*/templates.txt`)

Dla każdej kategorii stworzyliśmy szablony zdań w naturalnym języku polskim:

```
# Przykłady z data/name/templates.txt:
Mam na imię [name].
Nazywam się [name] [surname].
Pan [name] jest naszym klientem.
Pani [name] zgłosiła reklamację.
```

### 3. Szablony mieszane (`data/mixed_templates.txt`)

Zawierają zdania z wieloma kategoriami jednocześnie:

```
[name] [surname] mieszka w [city] przy ul. [address].
Klient [name] [surname], PESEL [pesel], nr tel. [phone].
Proszę o kontakt z [name] [surname] na adres [email].
```

---

## Proces generacji danych treningowych

### Etap 1: Wypełnianie szablonów (`data_generator.py`)

```python
# Pseudokod procesu:
for template in all_templates:
    for _ in range(repetitions):
        filled = fill_tags_with_random_values(template)
        bio_tagged = convert_to_bio_format(filled)
        training_data.append(bio_tagged)
```

**Przykład transformacji:**

```
Szablon:  "Mam na imię [name] i mieszkam w [city]."
Wypełniony: "Mam na imię Anna i mieszkam w Krakowie."
BIO format:
Mam       O
na        O
imię      O
Anna      B-name
i         O
mieszkam  O
w         O
Krakowie  B-city
.         O
```

### Etap 2: Augmentacja danych

Stosujemy augmentację poprzez:

1. **Wielokrotne wypełnianie** - każdy szablon wypełniamy różnymi wartościami
2. **Korupcja tekstu** (`utils.py`) - dodajemy losowe błędy typograficzne:
   - Zamiana wielkości liter
   - Usuwanie/dodawanie spacji
   - Literówki

```python
# Przykład korupcji:
"Jan Kowalski" → "jan kowalski"  # lowercase
"Jan Kowalski" → "JanKowalski"   # usunięcie spacji
"Jan Kowalski" → "Jan  Kowalski" # podwójna spacja
```

### Etap 3: Podział na zbiory

```
Dane treningowe: 80%
Dane walidacyjne: 10%
Dane testowe: 10%
```

Pliki wyjściowe:

- `resources/model/train.tsv`
- `resources/model/dev.tsv`
- `resources/model/test.tsv`

---

## Format danych

Używamy formatu TSV zgodnego z Flair:

```
-DOCSTART- O

Mam O
na O
imię O
Anna B-name
i O
mieszkam O
w O
Krakowie B-city
. O

-DOCSTART- O

Kolejne O
zdanie O
...
```

---

## Statystyki wygenerowanych danych

| Metryka                | Wartość                    |
| ---------------------- | -------------------------- |
| Liczba zdań            | ~50,000                    |
| Liczba tokenów         | ~500,000                   |
| Średnia długość zdania | ~10 tokenów                |
| Rozkład kategorii      | zbalansowany (augmentacja) |

---

## Walidacja jakości danych

1. **Sprawdzenie poprawności tagów BIO** - każdy `I-*` musi być poprzedzony `B-*` lub `I-*`
2. **Sprawdzenie pokrycia kategorii** - wszystkie 25 kategorii reprezentowane
3. **Ręczna weryfikacja próbki** - 100 losowych zdań sprawdzonych manualnie
