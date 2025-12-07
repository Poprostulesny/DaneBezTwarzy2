# -*- coding: utf-8 -*-
"""
Szybki system wypełniania tagów anonimizacji z odmianą gramatyczną.

Pipeline:
1. Model NER (Flair) wykrywa dane wrażliwe → tekst z tagami [IMIĘ], [MIASTO]
2. TagFiller zamienia tagi na wartości z data/{tag}/values.txt
3. Morfeusz2 odmienia w odpowiedni przypadek gramatyczny

Użycie:
    from template_filler import TagFiller
    
    filler = TagFiller()
    result = filler.fill("Pani [IMIĘ] [NAZWISKO] mieszka w [MIASTO].")
"""

from .filler import TagFiller, PolishInflector, generate_pesel

__all__ = [
    'TagFiller',
    'PolishInflector', 
    'generate_pesel',
]

__version__ = '3.0.0'
