"""
Configuration management for the Rockfall Prediction System
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages system configuration and settings"""
    
    def __init__(self):
        self.config_file = 'config.json'
        self.default_config = {
            'mine_name': 'Open Pit Mine Alpha',
            'coordinates': '45.123, -123.456',
            'sensor_count': 47,
            'model_update_interval': 60,  # minutes
            'data_retention_days': 90,
            'alert_cooldown': 15,  # minutes
            'max_alerts_per_hour': 5,
            'sensor_freq_index': 1,
            'use_dem': True,
            'use_drone': True,
            'use_weather': True,
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.7,
                'high': 0.85
            },
            'communication': {
                'sms_enabled': True,
                'email_enabled': True,
                'audio_enabled': True,
                'visual_enabled': True
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            self.config['updated_at'] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            self.config.update(updates)
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_api_status(self) -> Dict[str, bool]:
        """Check status of API keys"""
        return {
            'openai': os.getenv("OPENAI_API_KEY") is not None,
            'twilio': os.getenv("TWILIO_ACCOUNT_SID") is not None,
            'sendgrid': os.getenv("SENDGRID_API_KEY") is not None
        }
    
    def get_mine_parameters(self) -> Dict[str, Any]:
        """Get mine-specific parameters"""
        return {
            'name': self.config.get('mine_name', 'Unknown Mine'),
            'coordinates': self.config.get('coordinates', '0, 0'),
            'sensor_count': self.config.get('sensor_count', 47),
            'boundaries': self.config.get('mine_boundaries', [])
        }
    
    def get_alert_settings(self) -> Dict[str, Any]:
        """Get alert configuration"""
        return {
            'thresholds': self.config.get('risk_thresholds', self.default_config['risk_thresholds']),
            'cooldown': self.config.get('alert_cooldown', 15),
            'max_per_hour': self.config.get('max_alerts_per_hour', 5),
            'communication': self.config.get('communication', self.default_config['communication'])
        }
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        return self.save_config()