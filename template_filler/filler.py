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
from typing import Dict, List, Tuple, Optional
from pathlib import Path

try:
    import morfeusz2
    MORFEUSZ_AVAILABLE = True
except ImportError:
    MORFEUSZ_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"

# Mapowanie tagów anonimizacji na pliki z wartościami
TAG_MAPPING = {
    # Tagi w formacie [TAG] z anonymize.py
"$[name]": "NAME",
"$[surname]": "SURNAME",
"$[age]": "AGE",
"$[date-of-birth]": "DATE-OF-BIRTH",
"$[date]": "DATE",
"$[sex]": "SEX",
"$[religion]": "RELIGION",
"$[political-view]": "POLITICAL-VIEW",
"$[ethnicity]": "ETHNICITY",
"$[sexual-orientation]": "SEXUAL-ORIENTATION",
"$[health]": "HEALTH",
"$[relative]": "RELATIVE",
"$[city]": "CITY",
"$[address]": "ADDRESS",
"$[email]": "EMAIL",
"$[phone]": "PHONE",
"$[pesel]": "PESEL",
"$[document-number]": "DOCUMENT-NUMBER",
"$[company]": "COMPANY",
"$[school-name]": "SCHOOL-NAME",
"$[job-title]": "JOB-TITLE",
"$[bank-account]": "BANK-ACCOUNT",
"$[credit-card-number]": "CREDIT-CARD-NUMBER",
"$[username]": "USERNAME",
"$[secret]": "SECRET",
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

CASES = ['nom', 'gen', 'dat', 'acc', 'inst', 'loc', 'voc']


def generate_pesel() -> str:
    """Generuje losowy PESEL z poprawną sumą kontrolną."""
    year = random.randint(1940, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    if year >= 2000:
        year_code = year - 2000
        month_code = month + 20
    else:
        year_code = year - 1900
        month_code = month
    serial = random.randint(0, 999)
    gender_digit = random.randint(0, 9)
    pesel_10 = f"{year_code:02d}{month_code:02d}{day:02d}{serial:03d}{gender_digit}"
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    checksum = sum(int(d) * w for d, w in zip(pesel_10, weights))
    control_digit = (10 - (checksum % 10)) % 10
    return pesel_10 + str(control_digit)


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
            # Szukamy formy pojedynczej (sg) w danym przypadku
            # Preferujemy formy oznaczone jako rzeczowniki (subst) i pojedyncze
            candidates = []
            for form_tuple in forms:
                form = form_tuple[0]
                tags = form_tuple[2]
                tag_parts = tags.split(':')
                
                # Sprawdź czy to forma pojedyncza i w odpowiednim przypadku
                is_singular = 'sg' in tag_parts or any('sg' in p.split('.') for p in tag_parts)
                has_case = any(case in p.split('.') for p in tag_parts)
                
                if has_case and is_singular:
                    candidates.append((form, tags))
            
            # Preferuj formy męskie (m1) lub żeńskie (f) nad innymi
            for form, tags in candidates:
                if ':m1' in tags or ':f' in tags and form != word:
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
    
    NIE używa ML do wyboru wartości - tylko:
    1. Losowy wybór z listy kandydatów
    2. Odmiana gramatyczna przez Morfeusz2
    """
    
    def __init__(self):
        self.inflector = PolishInflector()
        self.candidates: Dict[str, List[str]] = {}
        self._load_candidates()
    
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
    
    def _get_value(self, tag: str, case: str) -> str:
        """Pobiera wartość dla tagu i odmienia ją."""
        category = TAG_MAPPING.get(tag)
        
        if not category:
            return tag  # Nieznany tag - zostaw
        
        # Tagi proceduralne
        if category.startswith('_'):
            generator = PROCEDURAL_GENERATORS.get(category)
            return generator() if generator else tag
        
        # Tagi z plików
        candidates = self.candidates.get(tag, [])
        if not candidates:
            return tag
        
        # Losowy wybór
        value = random.choice(candidates)
        
        # Odmiana jeśli potrzebna
        if case != 'nom':
            value = self.inflector.inflect_phrase(value, case)
        
        return value
    
    def fill(self, text: str) -> str:
        """
        Wypełnia wszystkie tagi w tekście.
        
        Args:
            text: Tekst z tagami [IMIĘ], [MIASTO] itd.
            
        Returns:
            Tekst z wypełnionymi i odmienionymi wartościami
        """
        result = text
        
        # Znajdź wszystkie tagi
        tag_pattern = r'\[[A-ZĘÓĄŚŁŻŹĆŃ_]+\]'
        
        # Przetwarzaj od końca (żeby nie przesunąć indeksów)
        matches = list(re.finditer(tag_pattern, result))
        
        for match in reversed(matches):
            tag = match.group(0)
            start, end = match.start(), match.end()
            
            # Wykryj wymagany przypadek
            case = self._detect_required_case(result, start)
            
            # Pobierz i odmień wartość
            value = self._get_value(tag, case)
            
            # Zamień
            result = result[:start] + value + result[end:]
        
        return result
    
    def fill_batch(self, texts: List[str]) -> List[str]:
        """Wypełnia listę tekstów (szybkie przetwarzanie wsadowe)."""
        return [self.fill(text) for text in texts]


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
        
        results = [filler.fill(line.strip()) if line.strip() else "" 
                   for line in lines]
        
        output = args.output or args.input.replace('.txt', '_filled.txt')
        with open(output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
        print(f"Zapisano: {output}")
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
                    print(f"  → {filler.fill(text)}")
            except (KeyboardInterrupt, EOFError):
                break
        return
    
    print(filler.fill(text))


if __name__ == "__main__":
    main()
