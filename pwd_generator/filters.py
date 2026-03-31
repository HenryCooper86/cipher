import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def filter_history_by_date(history: List[Dict], 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict]:
    filtered = []
    for entry in history:
        try:
            created_at = datetime.fromisoformat(entry['metadata']['created_at'])
            if start_date and created_at < start_date:
                continue
            if end_date and created_at > end_date:
                continue
            filtered.append(entry)
        except (KeyError, ValueError) as e:
            logger.warning(f"Skipping entry with invalid date: {e}")
            continue
    return filtered


def filter_history_by_service(history: List[Dict], service_query: str) -> List[Dict]:
    query = service_query.lower()
    return [e for e in history if query in e.get('metadata', {}).get('service', '').lower()]


def filter_history_by_strength(history: List[Dict], min_strength: Optional[str] = None) -> List[Dict]:
    strength_order = {'Weak': 1, 'Fair': 2, 'Good': 3, 'Strong': 4, 'Very Strong': 5}
    if not min_strength:
        return history
    
    min_level = strength_order.get(min_strength, 0)
    filtered = []
    for entry in history:
        strength = entry.get('metadata', {}).get('strength', 'Weak')
        if strength_order.get(strength, 0) >= min_level:
            filtered.append(entry)
    return filtered


def filter_history_by_entropy(history: List[Dict], min_entropy: float) -> List[Dict]:
    return [e for e in history if e.get('metadata', {}).get('entropy', 0) >= min_entropy]


def sort_history(history: List[Dict], 
                sort_by: str = 'date',
                reverse: bool = True) -> List[Dict]:
    if not history:
        return history
    
    sorted_history = history.copy()
    
    if sort_by == 'date':
        def get_date_key(x):
            try:
                return datetime.fromisoformat(x.get('metadata', {}).get('created_at', '1970-01-01'))
            except (ValueError, TypeError):
                return datetime(1970, 1, 1)
        sorted_history.sort(key=get_date_key, reverse=reverse)
    elif sort_by == 'service':
        sorted_history.sort(
            key=lambda x: x.get('metadata', {}).get('service', '').lower(),
            reverse=reverse
        )
    elif sort_by == 'strength':
        strength_order = {'Weak': 1, 'Fair': 2, 'Good': 3, 'Strong': 4, 'Very Strong': 5}
        sorted_history.sort(
            key=lambda x: strength_order.get(x.get('metadata', {}).get('strength', 'Weak'), 0),
            reverse=reverse
        )
    elif sort_by == 'entropy':
        sorted_history.sort(
            key=lambda x: x.get('metadata', {}).get('entropy', 0),
            reverse=reverse
        )
    
    return sorted_history
