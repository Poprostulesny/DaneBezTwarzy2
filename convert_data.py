# -*- coding: utf-8 -*-
"""
Konwerter danych z pliku 'Dane' do formatu mixed_templates.txt

Format wejściowy:
{tag} (opis po polsku) "zdanie 1" "zdanie 2" ...

Format wyjściowy (mixed_templates.txt):
zdanie 1
zdanie 2
...
"""

import re

def parse_dane_file(input_file: str = "Dane") -> list[str]:
    """
    Parsuje plik Dane i wyciąga zdania.
    Zwraca listę zdań (bez cudzysłowów).
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Znajdź wszystkie zdania w cudzysłowach
    # Wzorzec: "tekst" (może zawierać dowolne znaki oprócz cudzysłowu)
    sentences = re.findall(r'"([^"]+)"', content)
    
    # Usuń puste i odfiltruj duplikaty zachowując kolejność
    seen = set()
    unique_sentences = []
    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique_sentences.append(s)
    
    return unique_sentences


def save_to_mixed_templates(sentences: list[str], output_file: str = "mixed_templates.txt"):
    """
    Zapisuje zdania do pliku mixed_templates.txt.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in sentences:
            f.write(sentence + '\n')
    
    print(f"Zapisano {len(sentences)} zdań do {output_file}")


def main():
    print("Konwersja pliku Dane do mixed_templates.txt...")
    
    # Parsuj plik Dane
    sentences = parse_dane_file("data/Dane")
    print(f"Znaleziono {len(sentences)} unikalnych zdań")
    
    # Pokaż kilka przykładowych zdań
    print("\nPrzykładowe zdania:")
    for i, s in enumerate(sentences[:5]):
        print(f"  {i+1}. {s[:80]}..." if len(s) > 80 else f"  {i+1}. {s}")
    
    # Zapisz do pliku
    save_to_mixed_templates(sentences, "data/mixed_templates.txt")
    
    print("\nGotowe! Teraz możesz uruchomić data_generator.py")


if __name__ == "__main__":
    main()
