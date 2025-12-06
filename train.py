# -*- coding: utf-8 -*-
"""
Skrypt treningowy dla modelu NER używającego Flair + Transformer (HerBERT).

Uruchomienie:
    python train.py

Plik zapisze model w `config.MODEL_DIR`.
"""
import os
from typing import Optional

from flair.embeddings import TransformerWordEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

import config
from data_generator import generate_corpus


def train_model(corpus=None, epochs: int = 8, model_dir: Optional[str] = None):
    """
    Trenuje SequenceTagger na dostarczonym korpusie.

    Args:
        corpus: opcjonalny obiekt `flair.data.Corpus`. Jeśli None, wygeneruje przykładowy.
        epochs: maksymalna liczba epok treningu
        model_dir: miejsce zapisu modelu. Jeśli None, użyje `config.MODEL_DIR`

    Zwraca:
        obiekt ModelTrainer po zakończeniu (zawiera historię treningu)
    """
    if model_dir is None:
        model_dir = config.MODEL_DIR
    os.makedirs(model_dir, exist_ok=True)

    if corpus is None:
        # Dla szybkiej demonstracji generujemy mały korpus
        corpus = generate_corpus(n_per_template=200)

    # Przygotuj embeddings: HerBERT (allegro/herbert-base-cased)
    embeddings = TransformerWordEmbeddings(
        model='allegro/herbert-base-cased',
        fine_tune=True,
    )

    # Słownik tagów utworzony z korpusu
    tag_dictionary = corpus.make_label_dictionary(label_type=config.TAG_TYPE)

    # Utworzenie taggera sekwencyjnego
    tagger = SequenceTagger(
        hidden_size=256,
        embeddings=embeddings,
        tag_dictionary=tag_dictionary,
        tag_type=config.TAG_TYPE,
        use_crf=True,
    )

    trainer = ModelTrainer(tagger, corpus)
    trainer.train(
        model_dir,
        learning_rate=5e-5,
        mini_batch_size=8,
        max_epochs=epochs,
    )

    return trainer


if __name__ == "__main__":
    # Uruchomienie treningu (domyślnie krótko, można zmienić parametry)
    print("Generuję korpus i startuję trening — to może chwilę potrwać...")
    trainer = train_model(epochs=6)
    print("Trening zakończony. Model zapisany w:", config.MODEL_DIR)

