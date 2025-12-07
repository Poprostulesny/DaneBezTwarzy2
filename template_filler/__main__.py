#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI dla szybkiego wypełniania tagów anonimizacji.

Użycie:
    python -m template_filler "Pani [IMIĘ] [NAZWISKO] mieszka w [MIASTO]."
    python -m template_filler -i input.txt -o output.txt
"""

from .filler import main

if __name__ == "__main__":
    main()
