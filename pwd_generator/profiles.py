import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from pwd_generator.constants import DEFAULT_POLICY

logger = logging.getLogger(__name__)


class PasswordProfile:
    def __init__(self, name: str, policy: Dict[str, Any], template: Optional[str] = None):
        self.name = name
        self.policy = {**DEFAULT_POLICY, **policy}
        self.template = template
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'policy': self.policy,
            'template': self.template
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordProfile':
        return cls(
            name=data['name'],
            policy=data.get('policy', {}),
            template=data.get('template')
        )


class ProfileManager:
    def __init__(self, profiles_file: Optional[str] = None):
        if not profiles_file:
            profiles_file = Path.home() / '.pwd_generator_profiles.json'
        self.profiles_file = Path(profiles_file)
        self.profiles: Dict[str, PasswordProfile] = {}
        self.load_profiles()
    
    def load_profiles(self) -> None:
        """Load profiles from file."""
        if not self.profiles_file.exists():
            self._create_default_profiles()
            return
        
        try:
            with open(self.profiles_file, 'r') as f:
                data = json.load(f)
            
            self.profiles = {}
            for profile_data in data.get('profiles', []):
                profile = PasswordProfile.from_dict(profile_data)
                self.profiles[profile.name] = profile
            
            logger.info(f"Loaded {len(self.profiles)} profiles")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            self._create_default_profiles()
    
    def save_profiles(self) -> bool:
        """Save profiles to file."""
        try:
            data = {
                'profiles': [profile.to_dict() for profile in self.profiles.values()]
            }
            
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.profiles)} profiles")
            return True
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            return False
    
    def _create_default_profiles(self) -> None:
        """Create default profiles."""
        default_profiles = [
            PasswordProfile('banking', {
                'min_length': 20,
                'min_entropy': 80,
                'require_special': True
            }, 'readable'),
            PasswordProfile('social', {
                'min_length': 16,
                'min_entropy': 60,
                'require_special': True
            }, 'url_safe'),
            PasswordProfile('work', {
                'min_length': 18,
                'min_entropy': 70,
                'require_special': True
            }, 'readable'),
            PasswordProfile('email', {
                'min_length': 16,
                'min_entropy': 65,
                'require_special': True
            }, 'readable'),
            PasswordProfile('general', {
                'min_length': 12,
                'min_entropy': 60,
                'require_special': True
            }, None)
        ]
        
        for profile in default_profiles:
            self.profiles[profile.name] = profile
        
        self.save_profiles()
        logger.info("Created default profiles")
    
    def get_profile(self, name: str) -> Optional[PasswordProfile]:
        """Get a profile by name."""
        return self.profiles.get(name.lower())
    
    def list_profiles(self) -> List[str]:
        """List all profile names."""
        return list(self.profiles.keys())
    
    def add_profile(self, profile: PasswordProfile) -> bool:
        """Add or update a profile."""
        self.profiles[profile.name.lower()] = profile
        return self.save_profiles()
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        if name.lower() in self.profiles:
            del self.profiles[name.lower()]
            return self.save_profiles()
        return False
