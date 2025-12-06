# -*- coding: utf-8 -*-
"""
Skrypt inferencyjny — ładuje wytrenowany model i anonimizuje nowe teksty.

Funkcja główna: `anonymize(text)` — zwraca tekst z podmienionymi wykrytymi jednostkami.
"""
from typing import Optional
import os
import re

from flair.data import Sentence
from flair.models import SequenceTagger

import config


def _load_model(model_path: Optional[str] = None) -> SequenceTagger:
    """
    Ładuje model Flair. Jeśli model_path == None, próbuje kilku domyślnych nazw.

    Returns:
        załadowany SequenceTagger
    """
    if model_path is None:
        candidates = [
            os.path.join(config.MODEL_DIR, "best-model.pt"),
            os.path.join(config.MODEL_DIR, "final-model.pt"),
            os.path.join(config.MODEL_DIR, "checkpoint.pt"),
        ]
        for c in candidates:
            if os.path.exists(c):
                model_path = c
                break
        if model_path is None:
            raise FileNotFoundError(f"Nie znaleziono modelu w {config.MODEL_DIR}. Proszę wytrenować model najpierw.")

    tagger = SequenceTagger.load(model_path)
    return tagger


def anonymize(text: str, tagger: Optional[SequenceTagger] = None) -> str:
    """
    Anonimizuje tekst: wykryte jednostki NER są zastępowane przez odpowiadające tagi,
    np. wykryte CITY -> `{city}`.

    Args:
        text: wejściowy tekst (string)
        tagger: opcjonalny wcześniej załadowany model (SequenceTagger). Jeśli None, zostanie załadowany.

    Returns:
        anonymized_text: tekst ze zastąpionymi jednostkami
    """
    if tagger is None:
        tagger = _load_model()

    sentence = Sentence(text)
    tagger.predict(sentence)

    # Zbuduj mapa start_index -> (end_index, label)
    spans = sentence.get_spans(config.TAG_TYPE)
    start_map = {}
    for span in spans:
        # span.tokens[0].idx jest indeksem tokenu (1-based)
        start_idx = span.tokens[0].idx - 1
        end_idx = span.tokens[-1].idx - 1
        # etykieta może mieć format B-LABEL lub LABEL — bierzemy ostatnią część
        label = span.get_label(config.TAG_TYPE).value
        # usuń prefiksy B-/I- jeśli istnieją
        label = re.sub(r'^[BI]-', '', label)
        start_map[start_idx] = (end_idx, label)

    tokens = [t.text for t in sentence.tokens]
    out_tokens = []
    i = 0
    while i < len(tokens):
        if i in start_map:
            end_idx, label = start_map[i]
            tag = config.ANONYMIZE_TAGS.get(label, "{anon}")
            out_tokens.append(tag)
            i = end_idx + 1
        else:
            out_tokens.append(tokens[i])
            i += 1

    # Złącz z pojedynczą spacją — dla prostoty
    return " ".join(out_tokens)


if __name__ == "__main__":
    # Krótkie demo: wczytaj model i spróbuj z przykładowym zdaniem
    try:
        tagger = _load_model()
    except FileNotFoundError as e:
        print(e)
        print("Uruchom `python train.py` aby wytrenować model przed użyciem inferencji.")
        raise

    sample = "Nazywam się Jan Kowalski i mieszkam w Warszawie przy ul. Marszałkowskiej 10."
    print("Przed:", sample)
    print("Po:", anonymize(sample, tagger=tagger))

