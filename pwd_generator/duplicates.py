import logging
from typing import List, Dict, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


def find_duplicate_passwords(history: List[Dict]) -> List[Tuple[str, List[int]]]:
    """Find duplicate passwords in history."""
    password_indices = {}
    
    for i, entry in enumerate(history):
        pwd = entry.get('password', '')
        if pwd:
            if pwd not in password_indices:
                password_indices[pwd] = []
            password_indices[pwd].append(i)
    
    duplicates = [(pwd, indices) for pwd, indices in password_indices.items() if len(indices) > 1]
    return duplicates


def find_similar_passwords(history: List[Dict], threshold: float = 0.8) -> List[Tuple[int, int, float]]:
    """
    Find similar passwords using Levenshtein distance.
    
    Returns list of (index1, index2, similarity_ratio) tuples.
    """
    from difflib import SequenceMatcher
    
    similar = []
    
    for i in range(len(history)):
        pwd1 = history[i].get('password', '')
        if not pwd1:
            continue
        
        for j in range(i + 1, len(history)):
            pwd2 = history[j].get('password', '')
            if not pwd2:
                continue
            
            similarity = SequenceMatcher(None, pwd1, pwd2).ratio()
            if similarity >= threshold:
                similar.append((i, j, similarity))
    
    return similar


def get_password_frequency(history: List[Dict]) -> Dict[str, int]:
    """Get frequency of each password."""
    passwords = [entry.get('password', '') for entry in history if entry.get('password')]
    return dict(Counter(passwords))
