# -*- coding: utf-8 -*-
"""
Skrypt treningowy dla modelu NER używającego Flair + Transformer (HerBERT).

Uruchomienie:
    python train.py

Plik zapisze model w `config.MODEL_DIR`.
"""
import os
from typing import Optional

import torch
from tqdm import tqdm
from flair.embeddings import TransformerWordEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

import config
from data_generator import generate_corpus


def train_model(corpus=None, epochs: int = 10, model_dir: Optional[str] = None, 
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
    
    print(f"✅ Korpus gotowy: train={len(corpus.train)}, dev={len(corpus.dev)}, test={len(corpus.test)}") # type: ignore

    # Etap 2: Ładowanie lub tworzenie modelu
    print("\n" + "="*60)
    print("🔤 ETAP 2/4: Ładowanie modelu...")
    print("="*60)
    
    # Sprawdź czy istnieje wcześniej wytrenowany model
    best_model_path = os.path.join(model_dir, "best-model.pt")
    final_model_path = os.path.join(model_dir, "final-model.pt")
    
    # Optymalizacje NVIDIA - włącz tylko gdy CUDA jest dostępna
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        torch.set_float32_matmul_precision("high")  # TF32 dla Tensor Cores (Ampere+)
        print(f"   🎮 GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("   ⚠️ CUDA niedostępna - trening na CPU (wolniejszy)")
    
    existing_model_path = None
    if os.path.exists(best_model_path):
        existing_model_path = best_model_path
    elif os.path.exists(final_model_path):
        existing_model_path = final_model_path
    
    if existing_model_path:
        print(f"   📂 Znaleziono istniejący model: {existing_model_path}")
        print("   ⏳ Ładowanie modelu do kontynuacji treningu...")
        tagger = SequenceTagger.load(existing_model_path)
        print("   ✅ Model załadowany! Kontynuacja treningu od ostatniego checkpointu.")
    else:
        print("   📂 Brak istniejącego modelu - tworzenie nowego...")
        
        # Ładowanie embeddingów tylko gdy tworzymy nowy model
        embeddings = TransformerWordEmbeddings(
            model='allegro/herbert-base-cased',
            fine_tune=True,
        )
        print("   ✅ Embeddingi HerBERT załadowane!")

        # Etap 3: Tworzenie modelu
        print("\n" + "="*60)
        print("🏗️  ETAP 3/4: Tworzenie modelu SequenceTagger...")
        print("="*60)
        
        # Słownik tagów utworzony z korpusu
        tag_dictionary = corpus.make_label_dictionary(label_type=config.TAG_TYPE)
        print(f"   Liczba etykiet NER: {len(tag_dictionary)}")

        # Budowanie loss_weights: niska waga dla O, wyższa dla tagów kontynuacyjnych (I-, E-)
        # aby model lepiej uczył się długich sekwencji (daty, adresy, artykuły ustaw)
        loss_weights = {'O': 0.1}  # Zmniejsz wagę klasy "O" (nie-encja)
        
        # Zwiększ wagę dla tagów I- i E- (kontynuacja i koniec encji)
        # To pomaga modelowi lepiej przewidywać wielotokenowe encje
        for tag in tag_dictionary.get_items():
            if tag.startswith('I-') or tag.startswith('E-'):
                loss_weights[tag] = 2.0  # Wyższa waga dla kontynuacji
        
        # Specjalnie zwiększ wagę dla DOCUMENT-NUMBER (często długie, trudne do wykrycia)
        # np. "art. 25 § 2 w zw. z art. 21 ust. 3 ustawy z dnia 01-12-2012"
        for tag in tag_dictionary.get_items():
            if 'DOCUMENT-NUMBER' in tag:
                loss_weights[tag] = 3.0  # Jeszcze wyższa waga dla numerów dokumentów
        
        print(f"   Loss weights: O=0.1, I-/E-=2.0, DOCUMENT-NUMBER=3.0")

        # Utworzenie taggera sekwencyjnego z loss weights
        tagger = SequenceTagger(
            hidden_size=512,  # Zwiększone z 256 dla lepszego modelowania długich sekwencji
            embeddings=embeddings,
            tag_dictionary=tag_dictionary,
            tag_type=config.TAG_TYPE,
            use_crf=True,  # CRF jest kluczowy dla spójności sekwencji BIO
            loss_weights=loss_weights,
            reproject_embeddings=True,  # Dodatkowa warstwa projekcji
        )
        print("   ✅ Nowy model utworzony!")
    
    total_params = sum(p.numel() for p in tagger.parameters())
    trainable_params = sum(p.numel() for p in tagger.parameters() if p.requires_grad)
    print(f"   Parametry modelu: {total_params/1e6:.2f}M (trenowalnych: {trainable_params/1e6:.2f}M)")

    # ---------------------------------------------
    # ETAP 4: Trening
    # ---------------------------------------------
    print("\n" + "="*60)
    print(f"🚀 ETAP 4/4: Trening modelu ({epochs} epok)...")
    print("="*60)

    from torch.optim import AdamW

    trainer = ModelTrainer(tagger, corpus)

    trainer.train(
        model_dir,
        learning_rate=1e-4,  # ≥ 0.0001
    # standardowy LR dla fine-tuningu
        mini_batch_size=64,
        use_amp=cuda_available,  # AMP tylko gdy CUDA dostępna
        max_epochs=epochs,
        train_with_dev=False,
        embeddings_storage_mode='none',
        optimizer=AdamW,
        use_final_model_for_eval=True,
        main_evaluation_metric=('micro avg', 'f1-score'),
     )

    print("\n" + "="*60)
    print("🎉 TRENING ZAKOŃCZONY!")
    print("="*60)

    return trainer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trening modelu NER dla języka polskiego")
    parser.add_argument("--epochs", type=int, default=20, help="Liczba epok treningu (domyślnie: 30)")
    parser.add_argument("--n-per-template", type=int, default=200, help="Liczba przykładów na szablon (domyślnie: 200, ignorowane gdy --max-sentences jest ustawione)")
    parser.add_argument("--max-sentences", type=int, default=50000, help="Maksymalna liczba zdań do wygenerowania (domyślnie: 30000)")
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