# -*- coding: utf-8 -*-
"""
Skrypt treningowy dla modelu NER używającego Flair + Transformer (HerBERT).

Uruchomienie:
    python train.py

Plik zapisze model w `config.MODEL_DIR`.
"""
import os
from typing import Optional

from tqdm import tqdm
from flair.embeddings import TransformerWordEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

import config
from data_generator import generate_corpus


def train_model(corpus=None, epochs: int = 8, model_dir: Optional[str] = None, 
                n_per_template: int = 200, max_sentences: Optional[int] = None):
    """
    Trenuje SequenceTagger na dostarczonym korpusie.

    Args:
        corpus: opcjonalny obiekt `flair.data.Corpus`. Jeśli None, wygeneruje przykładowy.
        epochs: maksymalna liczba epok treningu
        model_dir: miejsce zapisu modelu. Jeśli None, użyje `config.MODEL_DIR`
        n_per_template: liczba przykładów na szablon (używane gdy corpus=None i max_sentences=None)
        max_sentences: maksymalna liczba zdań do wygenerowania (równomiernie rozłożona po szablonach)

    Zwraca:
        obiekt ModelTrainer po zakończeniu (zawiera historię treningu)
    """
    if model_dir is None:
        model_dir = config.MODEL_DIR
    os.makedirs(model_dir, exist_ok=True)

    # Etap 1: Generowanie korpusu
    if corpus is None:
        print("\n" + "="*60)
        print("📊 ETAP 1/4: Generowanie korpusu treningowego...")
        print("="*60)
        corpus = generate_corpus(n_per_template=n_per_template, max_sentences=max_sentences)
    
    print(f"✅ Korpus gotowy: train={len(corpus.train)}, dev={len(corpus.dev)}, test={len(corpus.test)}")

    # Etap 2: Ładowanie embeddingów
    print("\n" + "="*60)
    print("🔤 ETAP 2/4: Ładowanie embeddingów HerBERT...")
    print("="*60)
    embeddings = TransformerWordEmbeddings(
        model='allegro/herbert-base-cased',
        fine_tune=True,
    )
    print("✅ Embeddingi załadowane!")

    # Etap 3: Tworzenie modelu
    print("\n" + "="*60)
    print("🏗️  ETAP 3/4: Tworzenie modelu SequenceTagger...")
    print("="*60)
    
    # Słownik tagów utworzony z korpusu
    tag_dictionary = corpus.make_label_dictionary(label_type=config.TAG_TYPE)
    print(f"   Liczba etykiet NER: {len(tag_dictionary)}")

    # Utworzenie taggera sekwencyjnego z loss weights
    tagger = SequenceTagger(
        hidden_size=256,
        embeddings=embeddings,
        tag_dictionary=tag_dictionary,
        tag_type=config.TAG_TYPE,
        use_crf=True,
        loss_weights={'O': 0.1},  # Zmniejsz wagę klasy "O" (nie-encja) żeby model uczył się encji
    )
    
    total_params = sum(p.numel() for p in tagger.parameters())
    trainable_params = sum(p.numel() for p in tagger.parameters() if p.requires_grad)
    print(f"   Parametry modelu: {total_params/1e6:.2f}M (trenowalnych: {trainable_params/1e6:.2f}M)")
    print("✅ Model utworzony!")

    # Etap 4: Trening
    print("\n" + "="*60)
    print(f"🚀 ETAP 4/4: Trening modelu ({epochs} epok)...")
    print("="*60)
    
    from torch.optim import AdamW
    from flair.optim import LinearSchedulerWithWarmup
    
    trainer = ModelTrainer(tagger, corpus)
    trainer.train(
        model_dir,
        learning_rate=5e-5,              # Standardowy LR dla fine-tuningu Transformerów
        mini_batch_size=16,              # Mniejszy batch dla stabilności z AdamW
        max_epochs=epochs,
        train_with_dev=False,            # Nie trenuj na dev
        embeddings_storage_mode='none',  # Oszczędność pamięci GPU
        optimizer=AdamW,
        weight_decay=0.01,               # Regularyzacja dla AdamW
        scheduler=LinearSchedulerWithWarmup,
        warmup_fraction=0.1,             # 10% kroków na warm-up
        main_evaluation_metric=('micro avg', 'f1-score'),  # Optymalizuj pod F1, nie loss
    )

    print("\n" + "="*60)
    print("🎉 TRENING ZAKOŃCZONY!")
    print("="*60)

    return trainer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trening modelu NER dla języka polskiego")
    parser.add_argument("--epochs", type=int, default=15, help="Liczba epok treningu (domyślnie: 15)")
    parser.add_argument("--n-per-template", type=int, default=200, help="Liczba przykładów na szablon (domyślnie: 200, ignorowane gdy --max-sentences jest ustawione)")
    parser.add_argument("--max-sentences", type=int, default=1000, help="Maksymalna liczba zdań do wygenerowania (domyślnie: 10000)")
    parser.add_argument("--model-dir", type=str, default=None, help="Katalog do zapisu modelu")
    args = parser.parse_args()    
    print("\n" + "="*60)
    print("🤖 DANE BEZ TWARZY - Trening modelu NER")
    print("="*60)
    print(f"   Epoki: {args.epochs}")
    print(f"   Maksymalna liczba zdań: {args.max_sentences}")
    print(f"   Katalog modelu: {args.model_dir or config.MODEL_DIR}")
    
    trainer = train_model(
        epochs=args.epochs,
        n_per_template=args.n_per_template,
        max_sentences=args.max_sentences,
        model_dir=args.model_dir
    )
    
    print(f"\n✅ Model zapisany w: {args.model_dir or config.MODEL_DIR}")

