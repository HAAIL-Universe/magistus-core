# config_loader.py

import yaml
import os

DEFAULT_CONFIG = {
    "agents_enabled": ["temporal_lobe", "prefrontal_cortex"],
    "voice_output": False,
    "debug_mode": False
}

def load_config(config_path: str = "config.yaml") -> dict:
    """
    Loads the YAML config file from the given path.

    :param config_path: Path to the config.yaml file
    :return: Dictionary of config values
    """
    if not os.path.exists(config_path):
        print(f"[WARNING] Config file not found at {config_path}. Using default config.")
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}. Using default config.")
        return DEFAULT_CONFIG
