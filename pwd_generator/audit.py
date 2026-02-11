import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)


class PasswordAuditor:
    def __init__(self, generator):
        self.gen = generator
    
    def find_duplicates(self) -> List[Tuple[str, List[int]]]:
        """Find duplicate passwords in history."""
        password_indices = {}
        duplicates = []
        
        for i, entry in enumerate(self.gen.history):
            pwd = entry.get('password', '')
            if pwd:
                if pwd not in password_indices:
                    password_indices[pwd] = []
                password_indices[pwd].append(i)
        
        for pwd, indices in password_indices.items():
            if len(indices) > 1:
                duplicates.append((pwd, indices))
        
        return duplicates
    
    def find_weak_passwords(self, min_entropy: float = 60.0) -> List[Tuple[int, Dict]]:
        """Find weak passwords in history."""
        weak = []
        
        for i, entry in enumerate(self.gen.history):
            entropy = entry.get('metadata', {}).get('entropy', 0)
            if entropy < min_entropy:
                weak.append((i, entry))
        
        return weak
    
    def find_expired_passwords(self) -> List[Tuple[int, Dict]]:
        """Find expired passwords."""
        expired = []
        expiration_days = self.gen.policy.get('expiration_days', 90)
        
        for i, entry in enumerate(self.gen.history):
            try:
                created_at = datetime.fromisoformat(entry['metadata']['created_at'])
                age = datetime.now() - created_at
                
                if age.days > expiration_days:
                    expired.append((i, entry))
            except (KeyError, ValueError):
                continue
        
        return expired
    
    def calculate_security_score(self) -> Dict[str, Any]:
        """Calculate overall security score."""
        if not self.gen.history:
            return {
                'score': 0,
                'max_score': 100,
                'percentage': 0,
                'details': {}
            }
        
        total = len(self.gen.history)
        weak_count = len(self.find_weak_passwords())
        duplicate_count = len(self.find_duplicates())
        expired_count = len(self.find_expired_passwords())
        
        strength_scores = {'Weak': 0, 'Fair': 1, 'Good': 2, 'Strong': 3, 'Very Strong': 4}
        avg_strength = sum(
            strength_scores.get(e.get('metadata', {}).get('strength', 'Weak'), 0)
            for e in self.gen.history
        ) / total if total > 0 else 0
        
        score = 100
        score -= (weak_count / total * 30) if total > 0 else 0
        score -= (duplicate_count / total * 20) if total > 0 else 0
        score -= (expired_count / total * 15) if total > 0 else 0
        score += (avg_strength / 4 * 10)
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 1),
            'max_score': 100,
            'percentage': round(score, 1),
            'details': {
                'total_passwords': total,
                'weak_passwords': weak_count,
                'duplicate_passwords': duplicate_count,
                'expired_passwords': expired_count,
                'average_strength': avg_strength
            }
        }
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        duplicates = self.find_duplicates()
        weak = self.find_weak_passwords()
        expired = self.find_expired_passwords()
        security_score = self.calculate_security_score()
        
        strength_distribution = Counter(
            e.get('metadata', {}).get('strength', 'Unknown')
            for e in self.gen.history
        )
        
        return {
            'generated_at': datetime.now().isoformat(),
            'security_score': security_score,
            'summary': {
                'total_passwords': len(self.gen.history),
                'duplicate_count': len(duplicates),
                'weak_count': len(weak),
                'expired_count': len(expired)
            },
            'duplicates': [
                {
                    'password': '***',
                    'length': len(pwd),
                    'count': len(indices),
                    'indices': indices
                }
                for pwd, indices in duplicates
            ],
            'weak_passwords': [
                {
                    'index': idx,
                    'service': entry.get('metadata', {}).get('service', ''),
                    'entropy': entry.get('metadata', {}).get('entropy', 0)
                }
                for idx, entry in weak
            ],
            'expired_passwords': [
                {
                    'index': idx,
                    'service': entry.get('metadata', {}).get('service', ''),
                    'created_at': entry.get('metadata', {}).get('created_at', '')
                }
                for idx, entry in expired
            ],
            'strength_distribution': dict(strength_distribution)
        }
