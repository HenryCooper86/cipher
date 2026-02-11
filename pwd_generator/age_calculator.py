import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def calculate_password_age(created_at: str) -> Dict[str, Any]:
    """Calculate password age and expiration status."""
    try:
        created = datetime.fromisoformat(created_at)
        now = datetime.now()
        age = now - created
        
        return {
            'age_days': age.days,
            'age_hours': age.seconds // 3600,
            'age_minutes': (age.seconds % 3600) // 60,
            'created_at': created_at,
            'is_expired': False,
            'days_until_expiry': None
        }
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to calculate password age: {e}")
        return {
            'age_days': 0,
            'age_hours': 0,
            'age_minutes': 0,
            'created_at': created_at,
            'is_expired': False,
            'days_until_expiry': None
        }


def check_expiration(created_at: str, expiration_days: int = 90) -> Dict[str, Any]:
    """Check if password is expired and days until expiry."""
    age_info = calculate_password_age(created_at)
    age_info['expiration_days'] = expiration_days
    age_info['is_expired'] = age_info['age_days'] > expiration_days
    
    if not age_info['is_expired']:
        age_info['days_until_expiry'] = expiration_days - age_info['age_days']
    else:
        age_info['days_overdue'] = age_info['age_days'] - expiration_days
    
    return age_info


def format_age(age_info: Dict[str, Any]) -> str:
    """Format age information as human-readable string."""
    if age_info['age_days'] > 365:
        years = age_info['age_days'] // 365
        days = age_info['age_days'] % 365
        return f"{years} year{'s' if years > 1 else ''}, {days} day{'s' if days != 1 else ''}"
    elif age_info['age_days'] > 0:
        return f"{age_info['age_days']} day{'s' if age_info['age_days'] != 1 else ''}"
    elif age_info['age_hours'] > 0:
        return f"{age_info['age_hours']} hour{'s' if age_info['age_hours'] != 1 else ''}"
    else:
        return f"{age_info['age_minutes']} minute{'s' if age_info['age_minutes'] != 1 else ''}"
