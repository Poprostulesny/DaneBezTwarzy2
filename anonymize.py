#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do anonimizacji danych osobowych w tekście.
Używa wytrenowanego modelu NER do wykrywania i maskowania wrażliwych informacji.

Użycie:
    # Anonimizacja tekstu z linii poleceń:
    python anonymize.py "Jan Kowalski mieszka w Warszawie"
    
    # Anonimizacja pliku:
    python anonymize.py -i input.txt -o output.txt
    
    # Anonimizacja ze standardowego wejścia:
    echo "Mój PESEL to 90010112345" | python anonymize.py
    
    # Użycie własnego modelu:
    python anonymize.py -m models/my_model "Tekst do anonimizacji"
"""

import argparse
import sys
import os
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Domyślne etykiety zastępcze dla różnych typów danych
DEFAULT_REPLACEMENTS = {
    "NAME": "[IMIĘ]",
    "SURNAME": "[NAZWISKO]",
    "AGE": "[WIEK]",
    "DATE-OF-BIRTH": "[DATA_URODZENIA]",
    "DATE": "[DATA]",
    "SEX": "[PŁEĆ]",
    "RELIGION": "[RELIGIA]",
    "POLITICAL-VIEW": "[POGLĄDY_POLITYCZNE]",
    "ETHNICITY": "[POCHODZENIE]",
    "SEXUAL-ORIENTATION": "[ORIENTACJA]",
    "HEALTH": "[ZDROWIE]",
    "RELATIVE": "[KREWNY]",
    "CITY": "[MIASTO]",
    "ADDRESS": "[ADRES]",
    "EMAIL": "[EMAIL]",
    "PHONE": "[TELEFON]",
    "PESEL": "[PESEL]",
    "DOCUMENT-NUMBER": "[NR_DOKUMENTU]",
    "COMPANY": "[FIRMA]",
    "SCHOOL-NAME": "[SZKOŁA]",
    "JOB-TITLE": "[STANOWISKO]",
    "BANK-ACCOUNT": "[KONTO_BANKOWE]",
    "CREDIT-CARD-NUMBER": "[KARTA_KREDYTOWA]",
    "USERNAME": "[UŻYTKOWNIK]",
    "SECRET": "[HASŁO]",
}


def load_model(model_path: str):
    """Ładuje wytrenowany model NER."""
    from flair.models import SequenceTagger
    
    if not os.path.exists(model_path):
        print(f"❌ Błąd: Model nie znaleziony w '{model_path}'")
        print("   Najpierw wytrenuj model używając: python train.py")
        sys.exit(1)
    
    print(f"📥 Ładowanie modelu z: {model_path}")
    tagger = SequenceTagger.load(model_path)
    print("✅ Model załadowany pomyślnie")
    return tagger


def anonymize_text(
    text: str,
    tagger,
    replacements: Optional[Dict[str, str]] = None,
    show_entities: bool = False
) -> Tuple[str, List[Dict]]:
    """
    Anonimizuje tekst zastępując wykryte encje.
    
    Args:
        text: Tekst do anonimizacji
        tagger: Załadowany model NER
        replacements: Słownik mapujący etykiety na tekst zastępczy
        show_entities: Czy wyświetlać wykryte encje
    
    Returns:
        Tuple[str, List[Dict]]: Zanonimizowany tekst i lista wykrytych encji
    """
    from flair.data import Sentence
    
    if replacements is None:
        replacements = DEFAULT_REPLACEMENTS
    
    # Przetwórz tekst przez model
    sentence = Sentence(text)
    tagger.predict(sentence)
    
    # Zbierz wykryte encje
    entities = []
    for entity in sentence.get_spans('ner'):
        entities.append({
            'text': entity.text,
            'label': entity.tag,
            'start': entity.start_position,
            'end': entity.end_position,
            'confidence': entity.score
        })
    
    if show_entities and entities:
        print("\n🔍 Wykryte encje:")
        for e in entities:
            print(f"   • '{e['text']}' → {e['label']} (pewność: {e['confidence']:.2%})")
    
    # Zamień encje od końca (żeby nie przesunąć indeksów)
    result = text
    for entity in sorted(entities, key=lambda x: x['start'], reverse=True):
        label = entity['label']
        replacement = replacements.get(label, f"[{label}]")
        result = result[:entity['start']] + replacement + result[entity['end']:]
    
    return result, entities


def anonymize_file(
    input_path: str,
    output_path: str,
    tagger,
    replacements: Optional[Dict[str, str]] = None,
    show_stats: bool = True
) -> Dict:
    """
    Anonimizuje plik tekstowy.
    
    Args:
        input_path: Ścieżka do pliku wejściowego
        output_path: Ścieżka do pliku wyjściowego
        tagger: Załadowany model NER
        replacements: Słownik mapujący etykiety na tekst zastępczy
        show_stats: Czy wyświetlać statystyki
    
    Returns:
        Dict: Statystyki anonimizacji
    """
    from tqdm import tqdm
    
    print(f"📂 Przetwarzanie pliku: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    anonymized_lines = []
    all_entities = []
    entity_counts = {}
    
    for line in tqdm(lines, desc="Anonimizacja", unit="linii"):
        if line.strip():
            anon_line, entities = anonymize_text(line, tagger, replacements)
            anonymized_lines.append(anon_line)
            all_entities.extend(entities)
            
            for e in entities:
                label = e['label']
                entity_counts[label] = entity_counts.get(label, 0) + 1
        else:
            anonymized_lines.append(line)
    
    # Zapisz wynik
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(anonymized_lines)
    
    stats = {
        'input_file': input_path,
        'output_file': output_path,
        'total_lines': len(lines),
        'total_entities': len(all_entities),
        'entity_counts': entity_counts
    }
    
    if show_stats:
        print(f"\n📊 Statystyki anonimizacji:")
        print(f"   • Przetworzono linii: {stats['total_lines']}")
        print(f"   • Znalezionych encji: {stats['total_entities']}")
        if entity_counts:
            print(f"   • Podział według typu:")
            for label, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
                print(f"      - {label}: {count}")
    
    print(f"\n✅ Zapisano zanonimizowany plik: {output_path}")
    return stats


def interactive_mode(tagger, replacements: Optional[Dict[str, str]] = None):
    """Tryb interaktywny - anonimizuj tekst wprowadzany przez użytkownika."""
    print("\n🔐 Tryb interaktywny - wpisz tekst do anonimizacji (Ctrl+C aby zakończyć)")
    print("-" * 60)
    
    try:
        while True:
            try:
                text = input("\n📝 Wprowadź tekst: ").strip()
                if not text:
                    continue
                
                result, entities = anonymize_text(text, tagger, replacements, show_entities=True)
                print(f"\n🔒 Zanonimizowany tekst:\n   {result}")
                
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\n\n👋 Zakończono tryb interaktywny")


def main():
    parser = argparse.ArgumentParser(
        description="Anonimizacja danych osobowych w tekście przy użyciu modelu NER",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  %(prog)s "Jan Kowalski mieszka w Warszawie"
  %(prog)s -i dane.txt -o anonimowe.txt
  %(prog)s -i dane.txt -o anonimowe.txt -m models/custom_model
  echo "Tekst" | %(prog)s
  %(prog)s --interactive
        """
    )
    
    parser.add_argument(
        'text',
        nargs='?',
        help='Tekst do anonimizacji (opcjonalnie)'
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Ścieżka do pliku wejściowego'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Ścieżka do pliku wyjściowego (domyślnie: input_anonymized.txt)'
    )
    
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='models/ner-model/best-model.pt',
        help='Ścieżka do modelu NER (domyślnie: models/ner-model/best-model.pt)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Uruchom w trybie interaktywnym'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Wyświetl szczegółowe informacje o wykrytych encjach'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Format wyjścia dla pojedynczego tekstu (domyślnie: text)'
    )
    
    args = parser.parse_args()
    
    # Załaduj model
    tagger = load_model(args.model)
    
    # Tryb interaktywny
    if args.interactive:
        interactive_mode(tagger)
        return
    
    # Przetwarzanie pliku
    if args.input:
        if not os.path.exists(args.input):
            print(f"❌ Błąd: Plik '{args.input}' nie istnieje")
            sys.exit(1)
        
        output = args.output
        if not output:
            input_path = Path(args.input)
            output = str(input_path.parent / f"{input_path.stem}_anonymized{input_path.suffix}")
        
        anonymize_file(args.input, output, tagger)
        return
    
    # Pojedynczy tekst z argumentu lub stdin
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        # Brak tekstu - pokaż pomoc
        parser.print_help()
        print("\n💡 Wskazówka: Użyj --interactive dla trybu interaktywnego")
        return
    
    # Anonimizuj tekst
    result, entities = anonymize_text(text, tagger, show_entities=args.verbose)
    
    if args.format == 'json':
        import json
        output = {
            'original': text,
            'anonymized': result,
            'entities': entities
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.format == 'csv':
        print("original,anonymized,entities_count")
        entities_str = ';'.join([f"{e['text']}:{e['label']}" for e in entities])
        print(f'"{text}","{result}",{len(entities)}')
    else:
        print(f"\n🔒 Wynik anonimizacji:\n{result}")


if __name__ == "__main__":
    main()
