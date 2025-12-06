# -*- coding: utf-8 -*-
"""
Generator syntetycznych danych NER dla języka polskiego.

Zasada działania:
- Pobieramy listę szablonów z `config.TEMPLATES` (użytkownik uzupełni je później).
- Dla każdego szablonu generujemy wartości (np. miasto, imię) przez `Faker('pl_PL')`.
- Opcjonalnie stosujemy korupcję (`utils.corrupt_text`) aby dane były bardziej odporne.
- Tworzymy obiekty `flair.data.Sentence` i przypisujemy tokenom odpowiednie tagi BIO.
"""
from typing import List, Tuple, Dict, Optional
import re
import random
from datetime import datetime, date
import os

from tqdm import tqdm

from faker import Faker

from flair.data import Sentence, Token, Span, Corpus
from flair.datasets import FlairDatapointDataset
def _generate_pesel() -> str:
    """
    Generates a valid synthetic PESEL number (11 digits).
    """
    # PESEL: YYMMDDPPPPK (K - checksum, simplified here)
    year = random.randint(50, 22)  # 1950-2022
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    serial = random.randint(1000, 9999)
    pesel = f"{year:02d}{month:02d}{day:02d}{serial:04d}"
    pesel = pesel[:11]  # ensure length
    return pesel

import config
from utils import corrupt_text


def _load_values_from_file(tag_name: str, data_dir: str = "data") -> List[str]:
    """
    Wczytuje wartości dla danego tagu z pliku `data/{tag_name}/values.txt`.
    """
    filepath = os.path.join(data_dir, tag_name, "values.txt")
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def _load_templates_from_file(tag_name: str, data_dir: str = "data") -> List[str]:
    """
    Wczytuje szablony dla danego tagu z pliku `data/{tag_name}/templates.txt`.
    """
    filepath = os.path.join(data_dir, tag_name, "templates.txt")
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def _get_value_for_placeholder(placeholder: str, values_cache: Dict[str, List[str]]) -> str:
    """
    Pobiera wartość dla placeholdera: szuka w cache (plikach),
    jeśli nie ma, generuje przez Faker (fallback).
    """
    key = placeholder.lower()
    
    # spróbuj załadować z cache
    if key in values_cache and values_cache[key]:
        return random.choice(values_cache[key])
    
    # fallback: Faker
    faker = Faker("pl_PL")
    if key in ("name", "fullname", "imie"):
        return faker.first_name()
    if key in ("surname", "lastname", "nazwisko"):
        return faker.last_name()
    if key in ("age",):
        return str(random.randint(0, 100))
    if key in ("date-of-birth", "date_of_birth", "dob"):
        dob = faker.date_of_birth(minimum_age=0, maximum_age=90)
        return dob.strftime("%d.%m.%Y")
    if key in ("date",):
        d = faker.date_between(start_date='-10y', end_date='today')
        if isinstance(d, (datetime, date)):
            return d.strftime("%d.%m.%Y")
        return str(d)
    if key in ("sex",):
        return random.choice(["mężczyzna", "kobieta"])
    if key in ("city", "miasto"):
        return faker.city()
    if key in ("email",):
        return faker.email()
    if key in ("phone",):
        return faker.phone_number()
    
    return faker.word()


def _generate_value_for_placeholder(placeholder: str, faker: Faker) -> str:
    """
    Zwraca wygenerowaną wartość dla zadanego placeholdera.

    Args:
        placeholder: nazwa pola jak w szablonie (np. 'city', 'name')
        faker: instancja Faker('pl_PL')

    Returns:
        wygenerowany string
    """
    key = placeholder.lower()
    # Imię / nazwisko
    if key in ("name", "fullname", "imie"):
        return faker.first_name()
    if key in ("surname", "lastname", "nazwisko"):
        return faker.last_name()

    # Wiek i daty
    if key in ("age",):
        return str(random.randint(0, 100))
    if key in ("date-of-birth", "date_of_birth", "dob"):
        dob = faker.date_of_birth(minimum_age=0, maximum_age=90)
        return dob.strftime("%d.%m.%Y")
    if key in ("date",):
        d = faker.date_between(start_date='-10y', end_date='today')
        if isinstance(d, (datetime, date)):
            return d.strftime("%d.%m.%Y")
        return str(d)

    # Płeć, religia, poglądy, pochodzenie, orientacja
    if key in ("sex",):
        return random.choice(["mężczyzna", "kobieta"])
    if key in ("religion",):
        return random.choice(["katolik", "bezwyznaniowy", "prawosławny", "protestant", "inne"])
    if key in ("political-view", "political_view"):
        return random.choice(["liberalne", "konserwatywne", "centrowe", "socjalistyczne", "prawicowe", "lewicowe"])
    if key in ("ethnicity",):
        return random.choice(["polskie", "ukraińskie", "romskie", "inne"])
    if key in ("sexual-orientation", "sexual_orientation"):
        return random.choice(["heteroseksualna", "homoseksualna", "biseksualna", "niezdefiniowana"])

    # Zdrowie, relacje
    if key in ("health",):
        return random.choice(["zdrowy", "cukrzyca", "nadciśnienie", "przewlekła choroba serca", "alergia"])
    if key in ("relative",):
        # generujemy krótką frazę np. 'mój brat Jan Kowalski'
        rel_tpl = random.choice(["mój brat {f} {l}", "syn {l}", "córka {l}", "żona {f} {l}"])
        return rel_tpl.format(f=faker.first_name(), l=faker.last_name())

    # Kontakt i identyfikatory
    if key in ("city", "miasto"):
        return faker.city()
    if key in ("address", "adres"):
        return f"{faker.street_name()} {faker.building_number()}, {faker.postcode()} {faker.city()}"
    if key in ("email",):
        return faker.email()
    if key in ("phone",):
        return faker.phone_number()
    if key in ("pesel",):
        return _generate_pesel()
    if key in ("document-number", "document_number"):
        return faker.bothify(text="??########")

    # Zawodowe / edukacyjne
    if key in ("company",):
        return faker.company()
    if key in ("school-name", "school_name"):
        return f"Szkoła {faker.city()} nr {random.randint(1,20)}"
    if key in ("job-title", "job_title"):
        return faker.job()

    # Finansowe i cyfrowe
    if key in ("bank-account", "bank_account"):
        # prosty, syntetyczny numer IBAN PL (PL + 26 cyfr)
        digits = "".join(str(random.randint(0, 9)) for _ in range(26))
        return f"PL{digits}"
    if key in ("credit-card-number", "credit_card_number"):
        try:
            return faker.credit_card_number()
        except Exception:
            return faker.bothify(text="####-####-####-####")
    if key in ("username",):
        return faker.user_name()
    if key in ("secret",):
        return faker.password(length=10)

    # fallback: zwróć słowo lub losowy token
    return faker.word()


def _find_subsequence(tokens: List[str], target: List[str]) -> Optional[Tuple[int, int]]:
    """
    Szuka podlisty `target` w `tokens` i zwraca indeks start/end (inclusive-exclusive),
    lub None gdy nie znaleziono.

    Porównanie jest uproszczone: normalizujemy znaki nie-alfanumeryczne i porównujemy lower-case.
    """
    def norm(s: str) -> str:
        return re.sub(r"\W+", "", s).lower()

    norm_tokens = [norm(t) for t in tokens]
    norm_target = [norm(t) for t in target]

    if not any(norm_target):
        return None

    L = len(norm_target)
    for i in range(len(norm_tokens) - L + 1):
        if norm_tokens[i:i+L] == norm_target:
            return i, i+L
    return None


def generate_corpus(n_per_template: int = 300, corrupt_prob: float = 0.25, seed: int = 42, 
                    data_dir: str = "data", max_sentences: Optional[int] = None) -> Corpus:
    """
    Generuje syntetyczny `flair.data.Corpus` na podstawie szablonów z `data/`.
    Wczytuje wartości i szablony z plików `data/{tag}/values.txt` i `data/{tag}/templates.txt`.

    Args:
        n_per_template: ile zdań wygenerować dla każdego szablonu (ignorowane gdy max_sentences jest ustawione)
        corrupt_prob: prawdopodobieństwo korupcji znaków w generowanych wartościach
        seed: seed losowości
        data_dir: katalog zawierający podfoldery z danymi
        max_sentences: maksymalna liczba zdań do wygenerowania (równomiernie rozłożona po szablonach)
                       Jeśli None, używa n_per_template dla każdego szablonu.

    Returns:
        Corpus z podziałem train/dev/test (80/10/10 domyślnie)
    """
    random.seed(seed)
    Faker.seed(seed)

    all_sentences: List[Sentence] = []

    # Załaduj szablony z plików (jeśli dostępne)
    all_templates = []
    placeholder_pattern = re.compile(r"\{([\w\-]+)\}")
    
    # Najpierw załaduj szablony z poszczególnych folderów tagów
    if os.path.exists(data_dir):
        for tag_dir in os.listdir(data_dir):
            tag_path = os.path.join(data_dir, tag_dir)
            if os.path.isdir(tag_path):
                templates = _load_templates_from_file(tag_dir, data_dir)
                all_templates.extend(templates)
    
    # Następnie załaduj szablony mieszane (jeśli plik istnieje)
    mixed_templates_file = "mixed_templates.txt"
    if os.path.exists(mixed_templates_file):
        with open(mixed_templates_file, 'r', encoding='utf-8') as f:
            mixed = [line.strip() for line in f if line.strip()]
            all_templates.extend(mixed)
    
    if not all_templates:
        all_templates = config.TEMPLATES
    
    # Cache wczytanych wartości
    values_cache: Dict[str, List[str]] = {}
    for label in config.LABELS:
        values_cache[label.lower()] = _load_values_from_file(label.lower(), data_dir)

    # Oblicz liczbę zdań na szablon
    num_templates = len(all_templates)
    
    if max_sentences is not None:
        # Równomierne rozłożenie zdań po szablonach
        # Każdy szablon dostaje co najmniej max_sentences // num_templates zdań
        # Reszta jest rozłożona losowo (pierwsze szablony dostają po 1 więcej)
        base_per_template = max_sentences // num_templates
        extra = max_sentences % num_templates
        
        # Lista: ile zdań dla każdego szablonu
        sentences_per_template = [base_per_template + (1 if i < extra else 0) for i in range(num_templates)]
        # Przemieszaj, żeby dodatkowe zdania nie trafiały zawsze do pierwszych szablonów
        random.shuffle(sentences_per_template)
        
        total_iterations = max_sentences
        print(f"   Szablonów: {num_templates}, zdań na szablon: ~{base_per_template} (łącznie: {max_sentences})")
    else:
        # Stary tryb: n_per_template dla każdego szablonu
        sentences_per_template = [n_per_template] * num_templates
        total_iterations = num_templates * n_per_template
        print(f"   Szablonów: {num_templates}, zdań na szablon: {n_per_template} (łącznie: {total_iterations})")
    
    with tqdm(total=total_iterations, desc="Generowanie zdań", unit="zdań") as pbar:
        for template_idx, template in enumerate(all_templates):
            n_sentences_for_this_template = sentences_per_template[template_idx]
            for _ in range(n_sentences_for_this_template):
                # znajdź placeholdery w szablonie
                placeholders = placeholder_pattern.findall(template)
                values: Dict[str, str] = {}
                for ph in placeholders:
                    raw_val = _get_value_for_placeholder(ph, values_cache)
                    # zastosuj korupcję z pewnym prawdopodobieństwem
                    if random.random() < 0.5:
                        # 50% szansy na próbę korupcji
                        val = corrupt_text(raw_val, prob=corrupt_prob)
                    else:
                        val = raw_val
                    values[ph] = val

                sentence_text = template.format(**values)
                sentence = Sentence(sentence_text)

                # Nie dodaj "O" na wszystko - Flair domyślnie traktuje tokeny bez tagu jako "O"
                # Dodaj tylko tagi encji (B-, I-)

                # Dla każdego placeholdera znajdź jego miejsce w tokenach i przypisz BIO
                for ph in placeholders:
                    entity_value = values[ph]
                    # Tokenizuj wartość przy użyciu tokenizera Flair, aby dopasowanie
                    # było spójne z tokenizacją zdania (zamiast prostego .split()).
                    target_sent = Sentence(entity_value)
                    target_tokens = [t.text for t in target_sent.tokens]
                    token_texts = [t.text for t in sentence.tokens]
                    found = _find_subsequence(token_texts, target_tokens)
                    label = ph.upper()
                    if found is None:
                        # Jeżeli nie znaleziono (rzadko), pomijamy to wystąpienie
                        continue
                    start, end = found
                    # Stwórz Span object (prawidłowy sposób dla Flair)
                    span = Span(sentence.tokens[start:end])
                    span.add_label(config.TAG_TYPE, label)

                all_sentences.append(sentence)
                pbar.update(1)

    # Podział na zbiory: 80/10/10
    random.shuffle(all_sentences)
    n = len(all_sentences)
    n_train = int(0.8 * n)
    n_dev = int(0.1 * n)
    train_sentences = all_sentences[:n_train]
    dev_sentences = all_sentences[n_train:n_train + n_dev]
    test_sentences = all_sentences[n_train + n_dev:]

    # Użyj FlairDatapointDataset, wymaganego przez nową wersję Flair
    train_dataset = FlairDatapointDataset(train_sentences)
    dev_dataset = FlairDatapointDataset(dev_sentences)
    test_dataset = FlairDatapointDataset(test_sentences)

    return Corpus(train=train_dataset, dev=dev_dataset, test=test_dataset)


if __name__ == "__main__":
    # Krótka demonstracja: wygeneruj mały korpus i zapisz w formacie konsoli
    corpus = generate_corpus(n_per_template=5)
    print(f"Wygenerowano: train={len(corpus.train) if corpus.train else 0}, dev={len(corpus.dev) if corpus.dev else 0}, test={len(corpus.test) if corpus.test else 0}")

