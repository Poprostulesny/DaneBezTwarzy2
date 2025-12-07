# -*- coding: utf-8 -*-
"""
Szybki system wypełniania tagów anonimizacji z odmianą gramatyczną.

Pipeline:
1. Model NER (Flair) wykrywa i taguje dane wrażliwe → tekst z tagami [IMIĘ], [MIASTO]
2. Ten moduł zamienia tagi na losowe wartości z data/{tag}/values.txt
3. Morfeusz2 odmienia wartości w odpowiedni przypadek gramatyczny

Wydajność: ~1000 zdań/sekundę (bez ML przy wypełnianiu!)
"""

import re
import random
import time
import os
from datetime import date
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

try:
    import morfeusz2
    MORFEUSZ_AVAILABLE = True
except ImportError:
    MORFEUSZ_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"

# Mapowanie tagów anonimizacji na pliki z wartościami
TAG_MAPPING = {
    # Tagi w formacie [TAG] z anonymize.py -> nazwy folderów w data/
    "[NAME]": "name",
    "[SURNAME]": "surname",
    "[AGE]": "age",
    "[DATE-OF-BIRTH]": "date-of-birth",
    "[DATE]": "date",
    "[SEX]": "sex",
    "[RELIGION]": "religion",
    "[POLITICAL-VIEW]": "political-view",
    "[ETHNICITY]": "ethnicity",
    "[SEXUAL-ORIENTATION]": "sexual-orientation",
    "[HEALTH]": "health",
    "[RELATIVE]": "relative",
    "[CITY]": "city",
    "[ADDRESS]": "address",
    "[EMAIL]": "email",
    "[PHONE]": "phone",
    "[PESEL]": "pesel",
    "[DOCUMENT-NUMBER]": "document-number",
    "[COMPANY]": "company",
    "[SCHOOL-NAME]": "school-name",
    "[JOB-TITLE]": "job-title",
    "[BANK-ACCOUNT]": "bank-account",
    "[CREDIT-CARD-NUMBER]": "credit-card-number",
    "[USERNAME]": "username",
    "[SECRET]": "secret",
}

# Przyimki wymagające konkretnych przypadków
# Uwaga: niektóre przyimki mają różne znaczenia z różnymi przypadkami
# np. "z" + inst = "z kimś", "z" + gen = "z miejsca"
PREPOSITION_CASES = {
    # Dopełniacz (gen) - skąd? od kogo?
    'do': 'gen', 'od': 'gen', 'bez': 'gen', 'dla': 'gen',
    'koło': 'gen', 'obok': 'gen', 'naprzeciw': 'gen', 'u': 'gen',
    'z': 'gen',  # "z Warszawy" (skąd)
    'ze': 'gen',
    # Celownik (dat) - komu?
    'ku': 'dat', 'dzięki': 'dat', 'przeciw': 'dat', 'przeciwko': 'dat',
    # Biernik (acc) - kogo? co? dokąd?
    'przez': 'acc', 'pro': 'acc', 'mimo': 'acc',
    # Narzędnik (inst) - z kim? czym?
    'przed': 'inst', 'między': 'inst', 'pomiędzy': 'inst',
    'nad': 'inst', 'pod': 'inst', 'za': 'inst',
    # Miejscownik (loc) - gdzie? o czym?
    'w': 'loc', 'we': 'loc', 'na': 'loc', 'o': 'loc', 'po': 'loc',
    'przy': 'loc',
}

# Słowa wymagające dopełniacza
GENITIVE_TRIGGERS = {'pana', 'pani', 'państwa', 'panny', 'pań'}

# Wzorce do wykrywania płci z kontekstu
FEMALE_INDICATORS = {
    # Tytuły
    'pani', 'panna', 'panią', 'pannie', 'panny',
    # Zaimki
    'ona', 'jej', 'ją', 'niej', 'nią',
    # Końcówki czasowników (sprawdzane osobno)
}

MALE_INDICATORS = {
    # Tytuły
    'pan', 'panem', 'panu', 'pana',
    # Zaimki
    'on', 'jego', 'go', 'jemu', 'mu', 'nim', 'niego',
}

# Końcówki czasowników wskazujące płeć
FEMALE_VERB_ENDINGS = ('łam', 'łaś', 'ła', 'łyśmy', 'łyście', 'ły')
MALE_VERB_ENDINGS = ('łem', 'łeś', 'ł', 'liśmy', 'liście', 'li')

CASES = ['nom', 'gen', 'dat', 'acc', 'inst', 'loc', 'voc']

# Tagi które są powiązane z kontekstem osoby
PERSON_TAGS = {'[NAME]', '[SURNAME]', '[AGE]', '[DATE-OF-BIRTH]', '[PESEL]', '[SEX]'}


def generate_pesel(birth_date: date = None, gender: str = None) -> str:
    """
    Generuje PESEL z poprawną sumą kontrolną.
    
    Args:
        birth_date: Data urodzenia (opcjonalna, losowa jeśli None)
        gender: 'M' lub 'F' (opcjonalna, losowa jeśli None)
    """
    if birth_date is None:
        year = random.randint(1940, 2005)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
    else:
        year = birth_date.year
        month = birth_date.month
        day = birth_date.day
    
    if year >= 2000:
        year_code = year - 2000
        month_code = month + 20
    else:
        year_code = year - 1900
        month_code = month
    
    serial = random.randint(0, 99)
    
    # Cyfra płci: nieparzysta = mężczyzna, parzysta = kobieta
    if gender == 'M':
        gender_digit = random.choice([1, 3, 5, 7, 9])
    elif gender == 'F':
        gender_digit = random.choice([0, 2, 4, 6, 8])
    else:
        gender_digit = random.randint(0, 9)
    
    pesel_10 = f"{year_code:02d}{month_code:02d}{day:02d}{serial:03d}{gender_digit}"
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    checksum = sum(int(d) * w for d, w in zip(pesel_10, weights))
    control_digit = (10 - (checksum % 10)) % 10
    return pesel_10 + str(control_digit)


@dataclass
class PersonContext:
    """
    Spójny kontekst osoby - wszystkie dane są ze sobą powiązane.
    
    gender → determinuje: name, surname, sex, cyfrę płci w PESEL
    birth_date → determinuje: age, date_of_birth, pierwsze 6 cyfr PESEL
    """
    gender: str  # 'M' lub 'F'
    birth_date: date
    name: str
    surname: str
    
    # Cache dla wygenerowanych wartości
    _pesel: str = field(default=None, repr=False)
    
    @property
    def age(self) -> int:
        """Wiek obliczony z daty urodzenia."""
        today = date.today()
        age = today.year - self.birth_date.year
        # Korekta jeśli urodziny jeszcze nie minęły w tym roku
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age
    
    @property
    def date_of_birth_str(self) -> str:
        """Data urodzenia jako string DD.MM.YYYY."""
        return self.birth_date.strftime("%d.%m.%Y")
    
    @property
    def pesel(self) -> str:
        """PESEL zgodny z datą urodzenia i płcią."""
        if self._pesel is None:
            object.__setattr__(self, '_pesel', generate_pesel(self.birth_date, self.gender))
        return self._pesel
    
    @property
    def sex(self) -> str:
        """Płeć jako słowo."""
        return "kobieta" if self.gender == 'F' else "mężczyzna"
    
    @classmethod
    def create(
        cls,
        gender: str = None,
        names_male: List[str] = None,
        names_female: List[str] = None,
        surnames_male: List[str] = None,
        surnames_female: List[str] = None
    ) -> 'PersonContext':
        """
        Tworzy nowy spójny kontekst osoby.
        
        Args:
            gender: 'M', 'F' lub None (losowe)
            names_male/female: Listy imion do wyboru
            surnames_male/female: Listy nazwisk do wyboru
        """
        # Losuj płeć jeśli nie podana
        if gender is None:
            gender = random.choice(['M', 'F'])
        
        # Losuj datę urodzenia (wiek 18-80 lat)
        today = date.today()
        min_year = today.year - 80
        max_year = today.year - 18
        birth_year = random.randint(min_year, max_year)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Bezpieczne dla wszystkich miesięcy
        birth_date = date(birth_year, birth_month, birth_day)
        
        # Wybierz imię i nazwisko zgodne z płcią
        if gender == 'F':
            name = random.choice(names_female) if names_female else "Anna"
            surname = random.choice(surnames_female) if surnames_female else "Kowalska"
        else:
            name = random.choice(names_male) if names_male else "Jan"
            surname = random.choice(surnames_male) if surnames_male else "Kowalski"
        
        return cls(
            gender=gender,
            birth_date=birth_date,
            name=name,
            surname=surname
        )


# Generatory dla tagów proceduralnych
PROCEDURAL_GENERATORS = {
    "_age": lambda: str(random.randint(18, 80)),
    "_date": lambda: f"{random.randint(1,28):02d}.{random.randint(1,12):02d}.{random.randint(1990,2024)}",
    "_date_of_birth": lambda: f"{random.randint(1,28):02d}.{random.randint(1,12):02d}.{random.randint(1940,2006)}",
    "_pesel": generate_pesel,
    "_phone": lambda: f"{random.randint(500,799)} {random.randint(100,999)} {random.randint(100,999)}",
    "_email": lambda: f"user{random.randint(1,9999)}@{random.choice(['gmail.com', 'wp.pl', 'onet.pl'])}",
    "_bank_account": lambda: " ".join([f"{random.randint(10,99)}" for _ in range(13)]),
    "_credit_card": lambda: " ".join([f"{random.randint(1000,9999)}" for _ in range(4)]),
    "_document": lambda: f"{random.choice(['ABC', 'XYZ', 'ASD'])}{random.randint(100000,999999)}",
    "_username": lambda: f"user_{random.randint(1,99999)}",
    "_secret": lambda: "********",
    "_sex": lambda: random.choice(["kobieta", "mężczyzna"]),
}


class PolishInflector:
    """Szybka odmiana polska używając Morfeusz2."""
    
    def __init__(self):
        if MORFEUSZ_AVAILABLE:
            self.morf = morfeusz2.Morfeusz(generate=True)
        else:
            self.morf = None
        self._cache: Dict[str, str] = {}
    
    def get_form(self, word: str, case: str) -> str:
        """Zwraca formę słowa w danym przypadku."""
        if not self.morf:
            return word
        
        cache_key = f"{word}:{case}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            forms = self.morf.generate(word)
            # Format tagów: "subst:sg:nom:m1" lub "subst:sg:gen.acc:m1"
            # Szukamy formy pojedynczej (sg) w danym przypadku
            candidates = []
            for form_tuple in forms:
                form = form_tuple[0]
                tags = form_tuple[2]  # np. "subst:sg:inst:m1"
                tag_parts = tags.split(':')
                
                # tag_parts = ['subst', 'sg', 'inst', 'm1'] lub ['subst', 'sg', 'gen.acc', 'm1']
                is_singular = len(tag_parts) > 1 and ('sg' in tag_parts[1] or tag_parts[1] == 'sg')
                
                # Przypadek może być połączony kropką, np. "gen.acc"
                case_part = tag_parts[2] if len(tag_parts) > 2 else ''
                case_options = case_part.split('.')
                has_case = case in case_options
                
                if has_case and is_singular:
                    candidates.append((form, tags))
            
            # Preferuj formy męskie (m1) lub żeńskie (f)
            for form, tags in candidates:
                if (':m1' in tags or ':f' in tags) and form != word:
                    self._cache[cache_key] = form
                    return form
            
            # Jeśli nie znaleziono preferowanej, weź pierwszą odmienioną
            for form, tags in candidates:
                if form != word:  # Preferuj formę różną od bazowej
                    self._cache[cache_key] = form
                    return form
            
            # Fallback - pierwsza znaleziona
            if candidates:
                self._cache[cache_key] = candidates[0][0]
                return candidates[0][0]
                
        except:
            pass
        
        self._cache[cache_key] = word
        return word
    
    def inflect_phrase(self, phrase: str, case: str) -> str:
        """Odmienia frazę wielowyrazową."""
        words = phrase.split()
        if len(words) == 1:
            return self.get_form(phrase, case)
        
        # Odmień każde słowo osobno
        inflected = [self.get_form(w, case) for w in words]
        return ' '.join(inflected)


class TagFiller:
    """
    Szybki system wypełniania tagów anonimizacji.
    
    Funkcje:
    1. Losowy wybór z listy kandydatów
    2. Odmiana gramatyczna przez Morfeusz2
    3. Wykrywanie płci z kontekstu i dopasowanie imion/nazwisk
    """
    
    def __init__(self):
        self.inflector = PolishInflector()
        self.candidates: Dict[str, List[str]] = {}
        self._load_candidates()
        # Cache dla imion/nazwisk podzielonych na płeć
        self._names_male: List[str] = []
        self._names_female: List[str] = []
        self._surnames_male: List[str] = []
        self._surnames_female: List[str] = []
        self._split_by_gender()
    
    def _load_candidates(self):
        """Ładuje listy wartości z plików."""
        for tag, category in TAG_MAPPING.items():
            if category.startswith('_'):
                continue  # Pomiń proceduralne
            
            filepath = DATA_DIR / category / "values.txt"
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    values = [line.strip() for line in f if line.strip()]
                if values:
                    self.candidates[tag] = values
    
    def _split_by_gender(self):
        """Dzieli imiona i nazwiska na męskie i żeńskie."""
        # Imiona - żeńskie kończą się na 'a' (w polskim)
        names = self.candidates.get("[NAME]", [])
        for name in names:
            if name and name[-1].lower() == 'a':
                self._names_female.append(name)
            else:
                self._names_male.append(name)
        
        # Nazwiska - żeńskie kończą się na 'a' (np. Kowalska vs Kowalski)
        surnames = self.candidates.get("[SURNAME]", [])
        for surname in surnames:
            if surname and surname[-1].lower() == 'a':
                self._surnames_female.append(surname)
            else:
                self._surnames_male.append(surname)
        
        # Jeśli brak podziału, użyj wszystkich
        if not self._names_male:
            self._names_male = names
        if not self._names_female:
            self._names_female = names
        if not self._surnames_male:
            self._surnames_male = surnames
        if not self._surnames_female:
            self._surnames_female = surnames
    
    def _detect_gender(self, text: str, tag_pos: int) -> Optional[str]:
        """
        Wykrywa płeć z kontekstu przed tagiem.
        
        Returns:
            'M' dla męskiej, 'F' dla żeńskiej, None gdy nieznana
        """
        # Pobierz tekst przed tagiem (max 100 znaków)
        before_text = text[max(0, tag_pos - 100):tag_pos].lower()
        words = before_text.split()
        
        if not words:
            return None
        
        # Sprawdź ostatnie słowa
        for word in reversed(words[-5:]):
            word_clean = word.rstrip('.,!?:;')
            
            # Sprawdź wskaźniki płci
            if word_clean in FEMALE_INDICATORS:
                return 'F'
            if word_clean in MALE_INDICATORS:
                return 'M'
            
            # Sprawdź końcówki czasowników
            for ending in FEMALE_VERB_ENDINGS:
                if word_clean.endswith(ending) and len(word_clean) > len(ending):
                    return 'F'
            for ending in MALE_VERB_ENDINGS:
                if word_clean.endswith(ending) and len(word_clean) > len(ending):
                    # Unikaj fałszywych dopasowań dla 'ł' (np. 'był' ale nie 'stół')
                    if ending == 'ł' and len(word_clean) < 4:
                        continue
                    return 'M'
        
        return None
    
    def _detect_required_case(self, text: str, tag_pos: int) -> str:
        """
        Wykrywa wymagany przypadek na podstawie kontekstu przed tagiem.
        
        Analizuje poprzedzające słowo (przyimek, tytuł) i zwraca przypadek.
        """
        # Pobierz tekst przed tagiem
        before_text = text[:tag_pos].lower()
        before = before_text.split()
        if not before:
            return 'nom'
        
        prev_word = before[-1].rstrip('.,!?:;')
        
        # Specjalne rozróżnienie dla "z" - narzędnik gdy towarzyszenie
        if prev_word in {'z', 'ze'}:
            # Szukaj czasowników wymagających narzędnika
            inst_verbs = {'spotkać', 'spotkał', 'spotkałem', 'spotkałam', 'spotka',
                          'rozmawia', 'rozmawiam', 'rozmawiać', 'rozmawiał',
                          'pracuje', 'pracować', 'pracował', 'współpracuje',
                          'mieszka', 'mieszkać', 'mieszkam', 'żyje', 'żyć',
                          'jedzie', 'idzie', 'idę', 'jadę', 'pojechał', 'poszedł'}
            # Sprawdź kilka poprzednich słów
            for w in before[-5:]:
                w_clean = w.rstrip('.,!?:;')
                if w_clean in inst_verbs or w_clean.startswith('spotk') or w_clean.startswith('rozmaw'):
                    return 'inst'
            # Domyślnie dopełniacz (z miejsca)
            return 'gen'
        
        # Sprawdź przyimki
        if prev_word in PREPOSITION_CASES:
            return PREPOSITION_CASES[prev_word]
        
        # Sprawdź tytuły wymagające dopełniacza
        if prev_word in GENITIVE_TRIGGERS:
            return 'gen'
        
        # Domyślnie mianownik
        return 'nom'
    
    def _get_value(self, tag: str, case: str, gender: Optional[str] = None) -> str:
        """Pobiera wartość dla tagu i odmienia ją."""
        category = TAG_MAPPING.get(tag)
        
        if not category:
            return tag  # Nieznany tag - zostaw
        
        # Tagi proceduralne
        if category.startswith('_'):
            generator = PROCEDURAL_GENERATORS.get(category)
            return generator() if generator else tag
        
        # Dla imion i nazwisk - użyj odpowiedniej płci
        if tag == "[NAME]" and gender:
            if gender == 'F' and self._names_female:
                value = random.choice(self._names_female)
            elif gender == 'M' and self._names_male:
                value = random.choice(self._names_male)
            else:
                value = random.choice(self.candidates.get(tag, [tag]))
        elif tag == "[SURNAME]" and gender:
            if gender == 'F' and self._surnames_female:
                value = random.choice(self._surnames_female)
            elif gender == 'M' and self._surnames_male:
                value = random.choice(self._surnames_male)
            else:
                value = random.choice(self.candidates.get(tag, [tag]))
        else:
            # Tagi z plików - standardowe
            candidates = self.candidates.get(tag, [])
            if not candidates:
                return tag
            value = random.choice(candidates)
        
        # Odmiana jeśli potrzebna
        if case != 'nom':
            value = self.inflector.inflect_phrase(value, case)
        
        return value
    
    def _get_value_from_context(self, tag: str, case: str, person: PersonContext) -> str:
        """Pobiera wartość z kontekstu osoby i odmienia ją."""
        if tag == "[NAME]":
            value = person.name
        elif tag == "[SURNAME]":
            value = person.surname
        elif tag == "[AGE]":
            return str(person.age)  # Wiek bez odmiany
        elif tag == "[DATE-OF-BIRTH]":
            return person.date_of_birth_str  # Data bez odmiany
        elif tag == "[PESEL]":
            return person.pesel  # PESEL bez odmiany
        elif tag == "[SEX]":
            value = person.sex
        else:
            return self._get_value(tag, case)
        
        # Odmiana jeśli potrzebna
        if case != 'nom':
            value = self.inflector.inflect_phrase(value, case)
        
        return value
    
    def _create_person_context(self, gender: Optional[str] = None) -> PersonContext:
        """Tworzy nowy kontekst osoby."""
        return PersonContext.create(
            gender=gender,
            names_male=self._names_male,
            names_female=self._names_female,
            surnames_male=self._surnames_male,
            surnames_female=self._surnames_female
        )
    
    def fill(self, text: str, return_time: bool = False):
        """
        Wypełnia wszystkie tagi w tekście.
        
        Tagi osobowe ([NAME], [SURNAME], [AGE], [DATE-OF-BIRTH], [PESEL], [SEX])
        są wypełniane spójnie - wszystkie odnoszą się do tej samej wygenerowanej osoby.
        
        Args:
            text: Tekst z tagami [NAME], [CITY] itd.
            return_time: Czy zwrócić również czas wykonania
            
        Returns:
            Tekst z wypełnionymi i odmienionymi wartościami
            Opcjonalnie: (tekst, czas_ms) gdy return_time=True
        """
        start_time = time.perf_counter()
        result = text
        
        # Znajdź wszystkie tagi w formacie [TAG-NAME]
        tag_pattern = r'\[[A-Z\-]+\]'
        matches = list(re.finditer(tag_pattern, result))
        
        # Sprawdź czy są tagi osobowe
        has_person_tags = any(m.group(0) in PERSON_TAGS for m in matches)
        
        # Wykryj płeć z kontekstu tekstu
        detected_gender: Optional[str] = None
        if has_person_tags:
            for match in matches:
                tag = match.group(0)
                if tag in PERSON_TAGS:
                    gender = self._detect_gender(result, match.start())
                    if gender:
                        detected_gender = gender
                        break
        
        # Stwórz kontekst osoby (jeden dla całego tekstu)
        person: Optional[PersonContext] = None
        if has_person_tags:
            person = self._create_person_context(detected_gender)
        
        # Przetwarzaj od końca (żeby nie przesunąć indeksów)
        for match in reversed(matches):
            tag = match.group(0)
            start, end = match.start(), match.end()
            
            # Wykryj wymagany przypadek
            case = self._detect_required_case(result, start)
            
            # Użyj kontekstu osoby dla tagów osobowych
            if tag in PERSON_TAGS and person:
                value = self._get_value_from_context(tag, case, person)
            else:
                value = self._get_value(tag, case)
            
            # Zamień
            result = result[:start] + value + result[end:]
        
        fill_time_ms = (time.perf_counter() - start_time) * 1000
        
        if return_time:
            return result, fill_time_ms
        return result
    
    def fill_batch(self, texts: List[str], return_time: bool = False):
        """Wypełnia listę tekstów (szybkie przetwarzanie wsadowe)."""
        start_time = time.perf_counter()
        results = [self.fill(text, return_time=False) for text in texts]
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        if return_time:
            return results, total_time_ms
        return results
    
    def fill_batch_parallel(
        self, 
        texts: List[str], 
        return_time: bool = False,
        max_workers: int = None,
        use_processes: bool = False
    ):
        """
        Wypełnia listę tekstów równolegle (multithreading/multiprocessing).
        
        Args:
            texts: Lista tekstów z tagami do wypełnienia
            return_time: Czy zwrócić również czas wykonania
            max_workers: Liczba wątków/procesów (domyślnie: liczba CPU)
            use_processes: Użyj procesów zamiast wątków (lepsze dla CPU-bound)
            
        Returns:
            Lista wypełnionych tekstów
            Opcjonalnie: (lista, czas_ms) gdy return_time=True
        """
        start_time = time.perf_counter()
        
        if max_workers is None:
            max_workers = os.cpu_count() or 4
        
        # Dla małych batch'ów - nie używaj wielowątkowości (overhead)
        if len(texts) < max_workers * 2:
            return self.fill_batch(texts, return_time)
        
        ExecutorClass = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        
        with ExecutorClass(max_workers=max_workers) as executor:
            results = list(executor.map(self.fill, texts))
        
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        if return_time:
            return results, total_time_ms
        return results


def main():
    """CLI do testowania."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Szybkie wypełnianie tagów anonimizacji"
    )
    parser.add_argument("text", nargs="?", help="Tekst z tagami do wypełnienia")
    parser.add_argument("-i", "--input", help="Plik wejściowy")
    parser.add_argument("-o", "--output", help="Plik wyjściowy")
    
    args = parser.parse_args()
    
    filler = TagFiller()
    print(f"Załadowano {len(filler.candidates)} kategorii wartości")
    if MORFEUSZ_AVAILABLE:
        print("Morfeusz2 aktywny - pełna odmiana gramatyczna")
    
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_time = time.perf_counter()
        results: List[str] = []
        for line in lines:
            if line.strip():
                filled = filler.fill(line.strip(), return_time=False)
                results.append(str(filled))
            else:
                results.append("")
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        output = args.output or args.input.replace('.txt', '_filled.txt')
        with open(output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
        print(f"Zapisano: {output}")
        print(f"⏱️  Czas wypełniania: {total_time_ms:.2f} ms ({len(lines)} linii)")
        return
    
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        # Tryb interaktywny
        print("\nTryb interaktywny. Wpisz tekst z tagami:")
        while True:
            try:
                text = input("> ").strip()
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                if text:
                    result, fill_time = filler.fill(text, return_time=True)
                    print(f"  → {result}")
                    print(f"    ⏱️  Czas wypełniania: {fill_time:.2f} ms")
            except (KeyboardInterrupt, EOFError):
                break
        return
    
    result, fill_time = filler.fill(text, return_time=True)
    print(result)
    print(f"\n⏱️  Czas wypełniania: {fill_time:.2f} ms")


if __name__ == "__main__":
    main()
