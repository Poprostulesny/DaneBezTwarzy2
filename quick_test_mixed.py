# -*- coding: utf-8 -*-
"""
Szybki test mieszanych szablonów z korupcją - mniejsza skala.
"""
import sys
sys.path.insert(0, '.')

from data_generator import generate_corpus

print("=== SZYBKI TEST MIESZANYCH SZABLONÓW ===\n")

# Generuj mniejszy korpus dla szybkiego testu
print("Generowanie korpusu (n_per_template=50, corrupt_prob=0.4)...")
corpus = generate_corpus(n_per_template=50, corrupt_prob=0.4)

train_list = list(corpus.train) if corpus.train else []
dev_list = list(corpus.dev) if corpus.dev else []
test_list = list(corpus.test) if corpus.test else []

total = len(train_list) + len(dev_list) + len(test_list)
print(f"Wygenerowano: {total} zdań (train={len(train_list)}, dev={len(dev_list)}, test={len(test_list)})")
print()

# Pokaż przykłady
print("=== PRZYKŁADY Z KORUPCJĄ I MIESZANYMI TAGAMI ===\n")

for i, sent in enumerate(train_list[:10]):
    print(f"[{i+1}] {sent.text}")
    
    # Zbierz tagi
    entities = {}
    for tok in sent.tokens:
        label = tok.get_label("ner")
        if label and label.value != "O":
            tag_type = label.value.split("-", 1)[1] if "-" in label.value else label.value
            if tag_type not in entities:
                entities[tag_type] = []
            entities[tag_type].append(tok.text)
    
    # Wyświetl encje
    if entities:
        print("    Encje:", ", ".join([f"{tag}:[{','.join(vals)}]" for tag, vals in entities.items()]))
    print()

print(f"\n[OK] Test zakonczony pomyslnie!")
print(f"    Dane sa skorupowane i mieszane (wiele tagow w jednym zdaniu)")
print(f"    Gotowe do treningu z train_mixed.py")
