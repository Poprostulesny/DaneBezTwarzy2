# -*- coding: utf-8 -*-
"""
Narzędzia pomocnicze dla projektu Dane bez twarzy.
Funkcje dotyczące wprowadzania szumów/korupcji tekstu.
"""
import random
from typing import Dict


def _default_leet_map() -> Dict[str, str]:
    """
    Zwraca domyślną mapę zamian znaków na tzw. leet-speak.
    Mapowanie jest uproszczone i wystarczające do generowania szumu.
    """
    return {
        "a": "@",
        "A": "@",
        "o": "0",
        "O": "0",
        "l": "1",
        "L": "1",
        "e": "3",
        "E": "3",
        "s": "$",
        "S": "$",
        "i": "1",
        "I": "1",
        "t": "+",
        "T": "+",
        "k": "|<",
        "K": "|<",
        "c": "(",
        "C": "(",
        "r": "®",
        "R": "®",
        "m": "^^",
        "M": "^^",
        "w": "vv",
        "W": "vv",
        "ó": "o",
        "Ó": "O",
        "ł": "l",
        "Ł": "L",
    }


def corrupt_text(text: str, prob: float = 0.4, leet_map: Dict[str, str] = None) -> str:
    """
    Zastosuj losowe zniekształcenia (leet-speak, zmianę liter, błędy OCR) do podanego tekstu.

    Args:
        text: wejściowy tekst (np. nazwa miasta, imię)
        prob: prawdopodobieństwo, że dany znak zostanie zamieniony (0..1), domyślnie 0.4 (bardziej agresywnie)
        leet_map: opcjonalna mapa zamian (jeśli None używana jest domyślna)

    Returns:
        zmodyfikowany (skorumpowany) tekst

    Uwaga: Funkcja aplikuje wiele typów błędów:
    - leet-speak (a→@, o→0, etc.)
    - błędy ortograficzne (zmiana losowych liter)
    - błędy OCR (podobne znaki)
    - czasami pominięcie znaku
    """
    if leet_map is None:
        leet_map = _default_leet_map()

    # Mapa podobnych liter (błędy OCR i typowe pomyłki)
    typo_map = {
        'a': ['e', 'o', '4'],
        'e': ['a', 'i', '3'],
        'i': ['e', 'l', '1'],
        'o': ['a', 'u', '0'],
        'u': ['o', 'v'],
        'l': ['i', '1'],
        'r': ['n', 'm'],
        's': ['z', '5', '$'],
        'z': ['s', 'x'],
        'c': ['e', 'o', '('],
        'n': ['m', 'h'],
        'h': ['n', 'b'],
        'm': ['n', 'rn'],
        'v': ['u', 'w'],
        'w': ['v', 'vv'],
    }

    out_chars = []
    for ch in text:
        r = random.random()
        
        # Najpierw spróbuj leet-speak
        if ch in leet_map and r < prob:
            out_chars.append(leet_map[ch])
        # Następnie spróbuj typo (zmianę na podobną literę)
        elif ch.lower() in typo_map and r < prob:
            replacement = random.choice(typo_map[ch.lower()])
            if ch.isupper() and replacement.isalpha():
                replacement = replacement.upper()
            out_chars.append(replacement)
        # Czasami pominięcie znaku (2% szansy)
        elif r < 0.02 and ch.isalpha():
            continue
        # Czasami duplikacja znaku (1% szansy)
        elif r < 0.03 and ch.isalpha():
            out_chars.append(ch)
            out_chars.append(ch)
        else:
            out_chars.append(ch)

    return "".join(out_chars)

