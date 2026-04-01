import json
import logging
from pathlib import Path
from typing import Any, Optional

from pwd_generator.constants import DEFAULT_POLICY

logger = logging.getLogger(__name__)

YAML_AVAILABLE = False
yaml = None

def _ensure_yaml():
    """Ensure PyYAML is available, install if needed."""
    global YAML_AVAILABLE, yaml

    if YAML_AVAILABLE:
        return True

    try:
        import yaml
        YAML_AVAILABLE = True
        return True
    except ImportError:
        from pwd_generator.dependency_checker import ensure_pyyaml
        if ensure_pyyaml():
            try:
                import yaml
                YAML_AVAILABLE = True
                return True
            except ImportError:
                pass
        return False


def load_config(config_file: Optional[str] = None) -> dict[str, Any]:
    if not config_file:
        config_file = Path.home() / '.pwd_generator_config.json'
    else:
        config_file = Path(config_file)

    if not config_file.exists():
        logger.debug(f"Config file not found: {config_file}, using defaults")
        return {'policy': DEFAULT_POLICY.copy()}

    try:
        with open(config_file, encoding='utf-8') as f:
            if config_file.suffix in ['.yaml', '.yml']:
                if not _ensure_yaml():
                    logger.error("YAML support not available, install PyYAML")
                    return {'policy': DEFAULT_POLICY.copy()}
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        if not isinstance(config, dict):
            logger.warning("Invalid config file format, using defaults")
            return {'policy': DEFAULT_POLICY.copy()}

        if 'policy' in config:
            policy = {**DEFAULT_POLICY, **config['policy']}
            config['policy'] = policy

        logger.info(f"Loaded config from {config_file}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON config: {e}")
        return {'policy': DEFAULT_POLICY.copy()}
    except OSError as e:
        logger.error(f"Failed to load config: {e}")
        return {'policy': DEFAULT_POLICY.copy()}


def save_config(config: dict[str, Any], config_file: Optional[str] = None) -> bool:
    if not config_file:
        config_file = Path.home() / '.pwd_generator_config.json'
    else:
        config_file = Path(config_file)

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            if config_file.suffix in ['.yaml', '.yml']:
                if not _ensure_yaml():
                    logger.error("YAML support not available, install PyYAML")
                    return False
                yaml.dump(config, f, default_flow_style=False)
            else:
                json.dump(config, f, indent=2)

        logger.info(f"Saved config to {config_file}")
        return True
    except (OSError, TypeError) as e:
        logger.error(f"Failed to save config: {e}")
        return False


def create_default_config(config_file: Optional[str] = None) -> bool:
    default_config = {
        'policy': DEFAULT_POLICY.copy(),
        'history': {
            'max_entries': 1000,
            'auto_cleanup': True
        },
        'export': {
            'default_format': 'json',
            'include_passwords': True
        }
    }
    return save_config(default_config, config_file)
