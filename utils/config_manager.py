"""Configuration management for AETHER system."""

import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
import os
from dataclasses import dataclass, asdict


@dataclass
class ConfigSchema:
    """Base configuration schema."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        return cls(**data)


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self._cache: Dict[str, Any] = {}
        self._env_prefix = "AETHER_"
    
    def load(self, config_name: str, format: str = "auto") -> Dict[str, Any]:
        """
        Load configuration file.
        
        Args:
            config_name: Name of configuration file (without extension)
            format: File format (json, yaml, or auto)
            
        Returns:
            Configuration dictionary
        """
        if config_name in self._cache:
            return self._cache[config_name]
        
        # Try different formats
        if format == "auto":
            for ext in [".yaml", ".yml", ".json"]:
                config_path = self.config_dir / f"{config_name}{ext}"
                if config_path.exists():
                    format = ext[1:]
                    break
            else:
                raise FileNotFoundError(f"Configuration '{config_name}' not found")
        else:
            ext = f".{format}" if not format.startswith(".") else format
            config_path = self.config_dir / f"{config_name}{ext}"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load file
        with open(config_path, 'r') as f:
            if format in ["yaml", "yml"]:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config, prefix=f"{self._env_prefix}{config_name.upper()}_")
        
        self._cache[config_name] = config
        return config
    
    def save(self, config_name: str, config: Dict[str, Any], format: str = "yaml"):
        """
        Save configuration to file.
        
        Args:
            config_name: Name of configuration file
            config: Configuration dictionary
            format: File format (json or yaml)
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        ext = f".{format}" if not format.startswith(".") else format
        config_path = self.config_dir / f"{config_name}{ext}"
        
        with open(config_path, 'w') as f:
            if format in ["yaml", "yml"]:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(config, f, indent=2)
        
        self._cache[config_name] = config
    
    def get(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            config_name: Configuration name
            key: Dot-separated key path (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.load(config_name)
        
        # Navigate nested structure
        value = config
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def set(self, config_name: str, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            config_name: Configuration name
            key: Dot-separated key path
            value: Value to set
        """
        config = self.load(config_name)
        
        # Navigate to parent
        parts = key.split('.')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        self._cache[config_name] = config
    
    def merge(self, config_name: str, updates: Dict[str, Any], deep: bool = True):
        """
        Merge updates into configuration.
        
        Args:
            config_name: Configuration name
            updates: Dictionary of updates
            deep: Perform deep merge
        """
        config = self.load(config_name)
        
        if deep:
            config = self._deep_merge(config, updates)
        else:
            config.update(updates)
        
        self._cache[config_name] = config
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        result = config.copy()
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert env var name to config path
                config_path = key[len(prefix):].lower().replace('_', '.')
                
                # Set value in config
                parts = config_path.split('.')
                current = result
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Try to parse value as JSON, otherwise use as string
                try:
                    current[parts[-1]] = json.loads(value)
                except json.JSONDecodeError:
                    current[parts[-1]] = value
        
        return result
    
    def validate(self, config_name: str, schema: Union[Dict[str, Any], ConfigSchema]) -> bool:
        """
        Validate configuration against schema.
        
        Args:
            config_name: Configuration name
            schema: Validation schema
            
        Returns:
            True if valid
        """
        config = self.load(config_name)
        
        if isinstance(schema, ConfigSchema):
            schema = schema.to_dict()
        
        return self._validate_against_schema(config, schema)
    
    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        # Simple validation - check required keys exist
        for key, value in schema.items():
            if key not in config:
                return False
            
            if isinstance(value, dict) and isinstance(config[key], dict):
                if not self._validate_against_schema(config[key], value):
                    return False
        
        return True