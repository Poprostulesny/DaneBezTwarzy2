# -*- coding: utf-8 -*-
"""
Konfiguracja projektu Dane bez twarzy.
Zawiera stałe, etykiety oraz ścieżki do zapisu modelu.
"""
from typing import List, Dict

# Pełny zestaw etykiet wymaganych przez użytkownika (bez B-/I- prefixów)
LABELS: List[str] = [
    "NAME",
    "SURNAME",
    "AGE",
    "DATE-OF-BIRTH",
    "DATE",
    "SEX",
    "RELIGION",
    "POLITICAL-VIEW",
    "ETHNICITY",
    "SEXUAL-ORIENTATION",
    "HEALTH",
    "RELATIVE",
    "CITY",
    "ADDRESS",
    "EMAIL",
    "PHONE",
    "PESEL",
    "DOCUMENT-NUMBER",
    "COMPANY",
    "SCHOOL-NAME",
    "JOB-TITLE",
    "BANK-ACCOUNT",
    "CREDIT-CARD-NUMBER",
    "USERNAME",
    "SECRET",
]

# Mapa etykiet do zastępczych tagów używanych przy anonimizacji
ANONYMIZE_TAGS: Dict[str, str] = {
    "NAME": "{name}",
    "SURNAME": "{surname}",
    "AGE": "{age}",
    "DATE-OF-BIRTH": "{date-of-birth}",
    "DATE": "{date}",
    "SEX": "{sex}",
    "RELIGION": "{religion}",
    "POLITICAL-VIEW": "{political-view}",
    "ETHNICITY": "{ethnicity}",
    "SEXUAL-ORIENTATION": "{sexual-orientation}",
    "HEALTH": "{health}",
    "RELATIVE": "{relative}",
    "CITY": "{city}",
    "ADDRESS": "{address}",
    "EMAIL": "{email}",
    "PHONE": "{phone}",
    "PESEL": "{pesel}",
    "DOCUMENT-NUMBER": "{document-number}",
    "COMPANY": "{company}",
    "SCHOOL-NAME": "{school-name}",
    "JOB-TITLE": "{job-title}",
    "BANK-ACCOUNT": "{bank-account}",
    "CREDIT-CARD-NUMBER": "{credit-card-number}",
    "USERNAME": "{username}",
    "SECRET": "{secret}",
}

# Ścieżka gdzie zapisany będzie wytrenowany model
MODEL_DIR: str = "resources/model"

# Typ taga używany przez Flair
TAG_TYPE: str = "ner"

# Przykładowe szablony (placeholdery dla każdego typu). Użytkownik może je zmienić.
TEMPLATES = [
    "Nazywam się {name} {surname} i mam {age} lat.",
    "Data urodzenia: {date-of-birth}.",
    "Przyjęto pacjenta dnia {date} z rozpoznaniem: {health}.",
    "Płeć: {sex}. Wyznanie: {religion}. Poglądy polityczne: {political-view}.",
    "Pochodzenie: {ethnicity}. Orientacja: {sexual-orientation}.",
    "Kontakt: e-mail {email}, tel. {phone}.",
    "PESEL: {pesel}, numer dokumentu: {document-number}.",
    "Adres zamieszkania: {address}, miasto: {city}.",
    "Pracuje w {company} na stanowisku {job-title}.",
    "Ukończył szkołę: {school-name}.",
    "Konto bankowe: {bank-account}, karta: {credit-card-number}.",
    "Użytkownik: {username}, sekrety: {secret}.",
    "Relacja: {relative}.",
]

