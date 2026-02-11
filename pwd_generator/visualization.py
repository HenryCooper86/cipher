import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_strength_color(strength: str) -> str:
    """Get color code for password strength."""
    colors = {
        'Weak': '\033[91m',      # Red
        'Fair': '\033[93m',      # Yellow
        'Good': '\033[92m',      # Green
        'Strong': '\033[94m',    # Blue
        'Very Strong': '\033[95m'  # Magenta
    }
    reset = '\033[0m'
    return colors.get(strength, '') + strength + reset


def get_strength_emoji(strength: str) -> str:
    """Get indicator for password strength."""
    indicators = {
        'Weak': '[WEAK]',
        'Fair': '[FAIR]',
        'Good': '[GOOD]',
        'Strong': '[STRONG]',
        'Very Strong': '[VERY STRONG]'
    }
    return indicators.get(strength, '[UNKNOWN]')


def display_strength_meter(password: str, entropy: float, strength: str, width: int = 50) -> str:
    """Display a visual strength meter bar."""
    max_entropy = 120
    bar_length = min(width, int((entropy / max_entropy) * width))
    filled = '█' * bar_length
    empty = '░' * (width - bar_length)
    emoji = get_strength_emoji(strength)
    
    return f"{emoji} [{filled}{empty}] {strength} ({entropy:.1f} bits)"


def display_character_breakdown(password: str) -> Dict[str, Any]:
    """Display breakdown of character types in password."""
    import string
    
    breakdown = {
        'uppercase': sum(1 for c in password if c in string.ascii_uppercase),
        'lowercase': sum(1 for c in password if c in string.ascii_lowercase),
        'digits': sum(1 for c in password if c in string.digits),
        'special': sum(1 for c in password if c in "@#$!?^&*~()[]=-_."),
        'total': len(password),
        'unique': len(set(password))
    }
    
    breakdown['percent_unique'] = (breakdown['unique'] / breakdown['total'] * 100) if breakdown['total'] > 0 else 0
    
    return breakdown


def format_character_breakdown(breakdown: Dict[str, Any]) -> str:
    """Format character breakdown as a visual display."""
    lines = []
    lines.append("Character Breakdown:")
    lines.append(f"  Uppercase: {'█' * min(20, breakdown['uppercase'])} {breakdown['uppercase']}")
    lines.append(f"  Lowercase: {'█' * min(20, breakdown['lowercase'])} {breakdown['lowercase']}")
    lines.append(f"  Digits:    {'█' * min(20, breakdown['digits'])} {breakdown['digits']}")
    lines.append(f"  Special:   {'█' * min(20, breakdown['special'])} {breakdown['special']}")
    lines.append(f"  Unique:    {breakdown['unique']}/{breakdown['total']} ({breakdown['percent_unique']:.1f}%)")
    
    return "\n".join(lines)


def print_enhanced_password_stats(gen, password: str, use_colors: bool = True) -> None:
    """Print enhanced password statistics with visualization."""
    from pwd_generator.utils import print_password_stats
    
    stats = gen.get_password_stats(password)
    breakdown = display_character_breakdown(password)
    
    print(f"\n{'='*70}")
    print(f"                    PASSWORD ANALYSIS")
    print(f"{'='*70}")
    
    print(f"\nPassword: {password}")
    print(f"\n{display_strength_meter(password, stats['entropy'], stats['strength'])}")
    
    print(f"\n{format_character_breakdown(breakdown)}")
    
    print(f"\nDetailed Stats:")
    print(f"  Length:         {stats['length']} characters")
    print(f"  Entropy:        {stats['entropy']:.2f} bits")
    print(f"  Strength:       {get_strength_emoji(stats['strength'])} {stats['strength']}")
    print(f"  Unique chars:   {stats['unique_chars']}")
    
    print(f"\nCharacter Types:")
    print(f"  Uppercase:    {'[YES]' if stats['has_uppercase'] else '[NO]'}")
    print(f"  Lowercase:    {'[YES]' if stats['has_lowercase'] else '[NO]'}")
    print(f"  Digits:       {'[YES]' if stats['has_digits'] else '[NO]'}")
    print(f"  Special:      {'[YES]' if stats['has_special'] else '[NO]'}")
    
    print(f"\nValidation:     {stats['validation_message']}")
    print(f"{'='*70}\n")
