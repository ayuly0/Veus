import json
import os
from typing import Any

class ConfigManager:
    """Manages persistent application settings."""
    
    DEFAULT_CONFIG = {
        "ssl_verify": None, # None means 'not set, ask once'
        "auto_load_proxies": False,
        "proxy_strategy": "round-robin",
        "api_version": 9,
        "timeout": 360.0,
        "show_proxy_logs": True
    }
    
    def __init__(self, path: str = "config.json"):
        self.path = path
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load config from file or return defaults."""
        if not os.path.exists(self.path):
            return self.DEFAULT_CONFIG.copy()
            
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**self.DEFAULT_CONFIG, **data}
        except Exception:
            return self.DEFAULT_CONFIG.copy()

    def save(self):
        """Save current config to file."""
        try:
            with open(self.path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()

    @property
    def all(self) -> dict[str, Any]:
        return self.config
