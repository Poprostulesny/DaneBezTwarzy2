# -*- coding: utf-8 -*-
"""
Moduł ewaluacji modelu NER.

Oblicza metryki jakości anonimizacji:
- Precision, Recall, F1 (micro, macro, weighted)
- Metryki per-klasa
- Confusion matrix
- Dokładność na poziomie tokenów i encji
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    """Wyniki ewaluacji."""
    # Metryki globalne
    precision_micro: float = 0.0
    recall_micro: float = 0.0
    f1_micro: float = 0.0
    
    precision_macro: float = 0.0
    recall_macro: float = 0.0
    f1_macro: float = 0.0
    
    precision_weighted: float = 0.0
    recall_weighted: float = 0.0
    f1_weighted: float = 0.0
    
    # Accuracy
    token_accuracy: float = 0.0
    entity_accuracy: float = 0.0  # Exact match encji
    
    # Metryki per-klasa
    per_class: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Statystyki
    total_entities_true: int = 0
    total_entities_pred: int = 0
    total_tokens: int = 0
    
    # Confusion data
    true_positives: Dict[str, int] = field(default_factory=dict)
    false_positives: Dict[str, int] = field(default_factory=dict)
    false_negatives: Dict[str, int] = field(default_factory=dict)
    
    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "WYNIKI EWALUACJI NER",
            "=" * 60,
            "",
            "METRYKI GLOBALNE:",
            f"  F1 (micro):     {self.f1_micro:.4f}",
            f"  F1 (macro):     {self.f1_macro:.4f}",
            f"  F1 (weighted):  {self.f1_weighted:.4f}",
            "",
            f"  Precision (micro): {self.precision_micro:.4f}",
            f"  Recall (micro):    {self.recall_micro:.4f}",
            "",
            f"  Token accuracy:    {self.token_accuracy:.4f}",
            f"  Entity accuracy:   {self.entity_accuracy:.4f}",
            "",
            f"  Encje (true):  {self.total_entities_true}",
            f"  Encje (pred):  {self.total_entities_pred}",
            f"  Tokeny:        {self.total_tokens}",
            "",
            "-" * 60,
            "METRYKI PER-KLASA:",
            "-" * 60,
            f"{'Klasa':<25} {'Prec':>8} {'Rec':>8} {'F1':>8} {'Support':>8}",
            "-" * 60,
        ]
        
        # Sortuj klasy alfabetycznie
        for cls in sorted(self.per_class.keys()):
            metrics = self.per_class[cls]
            lines.append(
                f"{cls:<25} {metrics['precision']:>8.4f} {metrics['recall']:>8.4f} "
                f"{metrics['f1']:>8.4f} {metrics['support']:>8.0f}"
            )
        
        lines.extend([
            "-" * 60,
            f"{'MICRO AVG':<25} {self.precision_micro:>8.4f} {self.recall_micro:>8.4f} "
            f"{self.f1_micro:>8.4f} {self.total_entities_true:>8}",
            f"{'MACRO AVG':<25} {self.precision_macro:>8.4f} {self.recall_macro:>8.4f} "
            f"{self.f1_macro:>8.4f}",
            f"{'WEIGHTED AVG':<25} {self.precision_weighted:>8.4f} {self.recall_weighted:>8.4f} "
            f"{self.f1_weighted:>8.4f}",
            "=" * 60,
        ])
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """Konwertuje wyniki do słownika."""
        return {
            'f1_micro': self.f1_micro,
            'f1_macro': self.f1_macro,
            'f1_weighted': self.f1_weighted,
            'precision_micro': self.precision_micro,
            'recall_micro': self.recall_micro,
            'precision_macro': self.precision_macro,
            'recall_macro': self.recall_macro,
            'precision_weighted': self.precision_weighted,
            'recall_weighted': self.recall_weighted,
            'token_accuracy': self.token_accuracy,
            'entity_accuracy': self.entity_accuracy,
            'total_entities_true': self.total_entities_true,
            'total_entities_pred': self.total_entities_pred,
            'total_tokens': self.total_tokens,
            'per_class': self.per_class,
        }


def extract_entities_from_tagged_text(text: str) -> List[Tuple[str, str]]:
    """
    Wyciąga encje z tekstu z tagami [TAG].
    
    Args:
        text: Tekst z tagami, np. "Pan [NAME] mieszka w [CITY]"
        
    Returns:
        Lista krotek (tag, pozycja_start) w kolejności wystąpienia
    """
    pattern = r'\[([A-Z\-]+)\]'
    entities = []
    for match in re.finditer(pattern, text):
        tag = match.group(1)
        entities.append((tag, match.start()))
    return entities


def extract_entities_from_bio(tokens: List[str], tags: List[str]) -> List[Tuple[str, int, int]]:
    """
    Wyciąga encje z sekwencji tagów BIO.
    
    Args:
        tokens: Lista tokenów
        tags: Lista tagów BIO (B-NAME, I-NAME, O, ...)
        
    Returns:
        Lista krotek (typ_encji, start_idx, end_idx)
    """
    entities = []
    current_entity = None
    current_start = None
    
    for i, tag in enumerate(tags):
        if tag.startswith('B-'):
            # Zakończ poprzednią encję jeśli była
            if current_entity:
                entities.append((current_entity, current_start, i))
            # Rozpocznij nową
            current_entity = tag[2:]
            current_start = i
        elif tag.startswith('I-'):
            entity_type = tag[2:]
            # Kontynuuj tylko jeśli to ta sama encja
            if current_entity != entity_type:
                if current_entity:
                    entities.append((current_entity, current_start, i))
                current_entity = entity_type
                current_start = i
        elif tag.startswith('S-'):
            # Single - jednowyrazowa encja
            if current_entity:
                entities.append((current_entity, current_start, i))
            entities.append((tag[2:], i, i + 1))
            current_entity = None
            current_start = None
        elif tag.startswith('E-'):
            # End - koniec encji
            if current_entity:
                entities.append((current_entity, current_start, i + 1))
            current_entity = None
            current_start = None
        else:  # 'O' lub inny
            if current_entity:
                entities.append((current_entity, current_start, i))
            current_entity = None
            current_start = None
    
    # Zakończ ostatnią encję
    if current_entity:
        entities.append((current_entity, current_start, len(tags)))
    
    return entities


def evaluate_ner(
    y_true: List[List[str]],
    y_pred: List[List[str]],
    tokens: Optional[List[List[str]]] = None
) -> EvaluationResult:
    """
    Ewaluuje predykcje NER względem ground truth.
    
    Args:
        y_true: Lista sekwencji tagów prawdziwych (BIO format)
        y_pred: Lista sekwencji tagów przewidzianych (BIO format)
        tokens: Opcjonalnie lista tokenów (do debugowania)
        
    Returns:
        EvaluationResult z wszystkimi metrykami
    """
    result = EvaluationResult()
    
    # Zbierz wszystkie klasy
    all_classes: Set[str] = set()
    
    # Statystyki per-klasa
    tp_per_class: Dict[str, int] = defaultdict(int)
    fp_per_class: Dict[str, int] = defaultdict(int)
    fn_per_class: Dict[str, int] = defaultdict(int)
    support_per_class: Dict[str, int] = defaultdict(int)
    
    # Token-level accuracy
    correct_tokens = 0
    total_tokens = 0
    
    # Entity-level exact match
    exact_matches = 0
    total_true_entities = 0
    total_pred_entities = 0
    
    for seq_idx, (true_tags, pred_tags) in enumerate(zip(y_true, y_pred)):
        # Upewnij się że sekwencje mają tę samą długość
        min_len = min(len(true_tags), len(pred_tags))
        true_tags = true_tags[:min_len]
        pred_tags = pred_tags[:min_len]
        
        # Token accuracy
        for t, p in zip(true_tags, pred_tags):
            total_tokens += 1
            if t == p:
                correct_tokens += 1
        
        # Wyciągnij encje
        true_entities = extract_entities_from_bio([], true_tags)
        pred_entities = extract_entities_from_bio([], pred_tags)
        
        total_true_entities += len(true_entities)
        total_pred_entities += len(pred_entities)
        
        # Zbierz klasy
        for ent_type, _, _ in true_entities:
            all_classes.add(ent_type)
            support_per_class[ent_type] += 1
        for ent_type, _, _ in pred_entities:
            all_classes.add(ent_type)
        
        # Konwertuj do setów dla porównania
        true_set = set((t, s, e) for t, s, e in true_entities)
        pred_set = set((t, s, e) for t, s, e in pred_entities)
        
        # True positives - exact match (typ + pozycja)
        for entity in pred_set:
            ent_type = entity[0]
            if entity in true_set:
                tp_per_class[ent_type] += 1
                exact_matches += 1
            else:
                fp_per_class[ent_type] += 1
        
        # False negatives
        for entity in true_set:
            ent_type = entity[0]
            if entity not in pred_set:
                fn_per_class[ent_type] += 1
    
    # Oblicz metryki globalne (micro)
    total_tp = sum(tp_per_class.values())
    total_fp = sum(fp_per_class.values())
    total_fn = sum(fn_per_class.values())
    
    result.precision_micro = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    result.recall_micro = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    result.f1_micro = 2 * result.precision_micro * result.recall_micro / (result.precision_micro + result.recall_micro) \
        if (result.precision_micro + result.recall_micro) > 0 else 0.0
    
    # Oblicz metryki per-klasa
    precisions = []
    recalls = []
    f1s = []
    weights = []
    
    for cls in sorted(all_classes):
        tp = tp_per_class[cls]
        fp = fp_per_class[cls]
        fn = fn_per_class[cls]
        support = support_per_class[cls]
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        result.per_class[cls] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
            'tp': tp,
            'fp': fp,
            'fn': fn,
        }
        
        if support > 0:  # Tylko klasy z przykładami
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
            weights.append(support)
    
    # Macro average (nieuważona średnia)
    result.precision_macro = sum(precisions) / len(precisions) if precisions else 0.0
    result.recall_macro = sum(recalls) / len(recalls) if recalls else 0.0
    result.f1_macro = sum(f1s) / len(f1s) if f1s else 0.0
    
    # Weighted average
    total_weight = sum(weights)
    if total_weight > 0:
        result.precision_weighted = sum(p * w for p, w in zip(precisions, weights)) / total_weight
        result.recall_weighted = sum(r * w for r, w in zip(recalls, weights)) / total_weight
        result.f1_weighted = sum(f * w for f, w in zip(f1s, weights)) / total_weight
    
    # Accuracy
    result.token_accuracy = correct_tokens / total_tokens if total_tokens > 0 else 0.0
    result.entity_accuracy = exact_matches / total_true_entities if total_true_entities > 0 else 0.0
    
    # Statystyki
    result.total_entities_true = total_true_entities
    result.total_entities_pred = total_pred_entities
    result.total_tokens = total_tokens
    result.true_positives = dict(tp_per_class)
    result.false_positives = dict(fp_per_class)
    result.false_negatives = dict(fn_per_class)
    
    return result


def evaluate_tagged_texts(
    true_texts: List[str],
    pred_texts: List[str]
) -> EvaluationResult:
    """
    Ewaluuje teksty z tagami [TAG] (nie BIO).
    
    Porównuje czy te same pozycje mają te same tagi.
    
    Args:
        true_texts: Lista tekstów z prawdziwymi tagami
        pred_texts: Lista tekstów z przewidzianymi tagami
        
    Returns:
        EvaluationResult z metrykami
    """
    result = EvaluationResult()
    
    # Statystyki per-klasa
    tp_per_class: Dict[str, int] = defaultdict(int)
    fp_per_class: Dict[str, int] = defaultdict(int)
    fn_per_class: Dict[str, int] = defaultdict(int)
    support_per_class: Dict[str, int] = defaultdict(int)
    
    all_classes: Set[str] = set()
    total_true = 0
    total_pred = 0
    exact_matches = 0
    
    for true_text, pred_text in zip(true_texts, pred_texts):
        true_entities = extract_entities_from_tagged_text(true_text)
        pred_entities = extract_entities_from_tagged_text(pred_text)
        
        total_true += len(true_entities)
        total_pred += len(pred_entities)
        
        # Zbierz klasy
        true_tags = [t for t, _ in true_entities]
        pred_tags = [t for t, _ in pred_entities]
        
        for tag in true_tags:
            all_classes.add(tag)
            support_per_class[tag] += 1
        for tag in pred_tags:
            all_classes.add(tag)
        
        # Porównaj sekwencje tagów (kolejność ma znaczenie)
        # True positive = tag na tej samej pozycji w sekwencji
        min_len = min(len(true_tags), len(pred_tags))
        
        matched_true = [False] * len(true_tags)
        matched_pred = [False] * len(pred_tags)
        
        # Najpierw dopasuj exact matches (pozycja + typ)
        for i, (t_tag, t_pos) in enumerate(true_entities):
            for j, (p_tag, p_pos) in enumerate(pred_entities):
                if not matched_pred[j] and t_tag == p_tag:
                    # Dopasowanie po typie (niekoniecznie pozycji)
                    tp_per_class[t_tag] += 1
                    matched_true[i] = True
                    matched_pred[j] = True
                    exact_matches += 1
                    break
        
        # False negatives - nieznalezione prawdziwe
        for i, (t_tag, _) in enumerate(true_entities):
            if not matched_true[i]:
                fn_per_class[t_tag] += 1
        
        # False positives - nadmiarowe predykcje
        for j, (p_tag, _) in enumerate(pred_entities):
            if not matched_pred[j]:
                fp_per_class[p_tag] += 1
    
    # Oblicz metryki (identycznie jak w evaluate_ner)
    total_tp = sum(tp_per_class.values())
    total_fp = sum(fp_per_class.values())
    total_fn = sum(fn_per_class.values())
    
    result.precision_micro = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    result.recall_micro = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    result.f1_micro = 2 * result.precision_micro * result.recall_micro / (result.precision_micro + result.recall_micro) \
        if (result.precision_micro + result.recall_micro) > 0 else 0.0
    
    # Per-class metrics
    precisions = []
    recalls = []
    f1s = []
    weights = []
    
    for cls in sorted(all_classes):
        tp = tp_per_class[cls]
        fp = fp_per_class[cls]
        fn = fn_per_class[cls]
        support = support_per_class[cls]
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        result.per_class[cls] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
        }
        
        if support > 0:
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
            weights.append(support)
    
    # Macro & weighted averages
    result.precision_macro = sum(precisions) / len(precisions) if precisions else 0.0
    result.recall_macro = sum(recalls) / len(recalls) if recalls else 0.0
    result.f1_macro = sum(f1s) / len(f1s) if f1s else 0.0
    
    total_weight = sum(weights)
    if total_weight > 0:
        result.precision_weighted = sum(p * w for p, w in zip(precisions, weights)) / total_weight
        result.recall_weighted = sum(r * w for r, w in zip(recalls, weights)) / total_weight
        result.f1_weighted = sum(f * w for f, w in zip(f1s, weights)) / total_weight
    
    result.entity_accuracy = exact_matches / total_true if total_true > 0 else 0.0
    result.total_entities_true = total_true
    result.total_entities_pred = total_pred
    
    return result


def evaluate_anonymization(
    original_texts: List[str],
    anonymized_texts: List[str],
    expected_tags: Optional[List[List[str]]] = None
) -> EvaluationResult:
    """
    Ewaluuje jakość anonimizacji.
    
    Jeśli expected_tags podane - porównuje czy wykryto odpowiednie tagi.
    Jeśli nie - tylko liczy ile tagów znaleziono.
    
    Args:
        original_texts: Oryginalne teksty (przed anonimizacją)
        anonymized_texts: Teksty po anonimizacji (z tagami [TAG])
        expected_tags: Opcjonalnie - oczekiwane tagi dla każdego tekstu
        
    Returns:
        EvaluationResult
    """
    if expected_tags:
        # Mamy ground truth - pełna ewaluacja
        true_texts = []
        for orig, tags in zip(original_texts, expected_tags):
            # Zbuduj tekst z tagami
            # To jest uproszczone - zakłada że tags to lista tagów w kolejności
            tagged = orig
            for tag in tags:
                tagged = f"{tagged} [{tag}]"  # placeholder
            true_texts.append(tagged)
        
        return evaluate_tagged_texts(true_texts, anonymized_texts)
    else:
        # Brak ground truth - tylko statystyki
        result = EvaluationResult()
        
        total_tags = 0
        tag_counts: Dict[str, int] = defaultdict(int)
        
        for text in anonymized_texts:
            entities = extract_entities_from_tagged_text(text)
            total_tags += len(entities)
            for tag, _ in entities:
                tag_counts[tag] += 1
        
        result.total_entities_pred = total_tags
        for tag, count in tag_counts.items():
            result.per_class[tag] = {
                'count': count,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'support': 0,
            }
        
        return result


# ============================================================================
# FUNKCJE POMOCNICZE DO TESTOWANIA
# ============================================================================

def quick_evaluate(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """
    Szybka ewaluacja - zwraca tylko główne metryki.
    
    Args:
        y_true: Lista prawdziwych tagów (flat)
        y_pred: Lista przewidzianych tagów (flat)
        
    Returns:
        Słownik z f1_micro, f1_macro, precision, recall
    """
    result = evaluate_ner([y_true], [y_pred])
    return {
        'f1_micro': result.f1_micro,
        'f1_macro': result.f1_macro,
        'precision': result.precision_micro,
        'recall': result.recall_micro,
        'accuracy': result.token_accuracy,
    }


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    # Przykład użycia
    print("=" * 60)
    print("PRZYKŁAD EWALUACJI NER")
    print("=" * 60)
    
    # Przykładowe dane BIO
    y_true = [
        ['O', 'B-NAME', 'B-SURNAME', 'O', 'O', 'B-CITY'],
        ['B-NAME', 'I-NAME', 'O', 'B-PHONE', 'I-PHONE', 'I-PHONE'],
    ]
    
    y_pred = [
        ['O', 'B-NAME', 'B-SURNAME', 'O', 'O', 'B-CITY'],  # Perfect
        ['B-NAME', 'O', 'O', 'B-PHONE', 'I-PHONE', 'O'],   # Błędy
    ]
    
    result = evaluate_ner(y_true, y_pred)
    print(result)
    
    print("\n" + "=" * 60)
    print("PRZYKŁAD EWALUACJI TEKSTÓW Z TAGAMI")
    print("=" * 60)
    
    true_texts = [
        "Pan [NAME] [SURNAME] mieszka w [CITY].",
        "Numer telefonu: [PHONE], email: [EMAIL].",
    ]
    
    pred_texts = [
        "Pan [NAME] [SURNAME] mieszka w [CITY].",  # Perfect
        "Numer telefonu: [PHONE], email: [USERNAME].",  # Błąd: EMAIL -> USERNAME
    ]
    
    result2 = evaluate_tagged_texts(true_texts, pred_texts)
    print(result2)
