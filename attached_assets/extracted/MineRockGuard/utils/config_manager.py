import json
import os
from datetime import datetime

class ConfigManager:
    def __init__(self):
        self.config_file = 'mine_config.json'
        self.default_config = {
            'mine_name': 'Open Pit Mine Alpha',
            'coordinates': '45.123, -123.456',
            'sensor_count': 47,
            'sensor_freq_index': 1,
            'model_update_interval': 60,
            'data_retention_days': 90,
            'alert_cooldown': 15,
            'max_alerts_per_hour': 5,
            'use_dem': True,
            'use_drone': True,
            'use_weather': True,
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.7,
                'high': 0.85
            },
            'notification_settings': {
                'sms_enabled': True,
                'email_enabled': True,
                'audio_enabled': True,
                'visual_enabled': True
            },
            'communication_settings': {
                'lorawan_enabled': True,
                'radio_backup_enabled': True,
                'satellite_backup_enabled': True
            },
            'system_settings': {
                'auto_retrain_model': True,
                'backup_frequency_hours': 24,
                'log_level': 'INFO',
                'max_log_size_mb': 100
            },
            'mine_zones': [
                {'id': 1, 'name': 'North Wall', 'risk_baseline': 0.2},
                {'id': 2, 'name': 'South Wall', 'risk_baseline': 0.3},
                {'id': 3, 'name': 'East Slope', 'risk_baseline': 0.4},
                {'id': 4, 'name': 'West Platform', 'risk_baseline': 0.2},
                {'id': 5, 'name': 'Central Pit', 'risk_baseline': 0.5},
                {'id': 6, 'name': 'Access Road North', 'risk_baseline': 0.1},
                {'id': 7, 'name': 'Access Road South', 'risk_baseline': 0.1},
                {'id': 8, 'name': 'Processing Area', 'risk_baseline': 0.2},
                {'id': 9, 'name': 'Equipment Zone', 'risk_baseline': 0.3},
                {'id': 10, 'name': 'Maintenance Area', 'risk_baseline': 0.2},
                {'id': 11, 'name': 'Emergency Exit 1', 'risk_baseline': 0.1},
                {'id': 12, 'name': 'Emergency Exit 2', 'risk_baseline': 0.1}
            ],
            'created_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        self.current_config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**self.default_config, **config}
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self, new_config=None):
        """Save configuration to file"""
        try:
            if new_config:
                self.current_config.update(new_config)
            
            self.current_config['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_current_config(self):
        """Get current configuration"""
        return self.current_config.copy()
    
    def get_config_value(self, key, default=None):
        """Get specific configuration value"""
        return self.current_config.get(key, default)
    
    def update_config_value(self, key, value):
        """Update specific configuration value"""
        self.current_config[key] = value
        return self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.current_config = self.default_config.copy()
        return self.save_config()
    
    def get_mine_zones(self):
        """Get mine zone configuration"""
        return self.current_config.get('mine_zones', [])
    
    def update_mine_zone(self, zone_id, zone_data):
        """Update specific mine zone configuration"""
        zones = self.current_config.get('mine_zones', [])
        for zone in zones:
            if zone['id'] == zone_id:
                zone.update(zone_data)
                break
        else:
            # Add new zone if not found
            zone_data['id'] = zone_id
            zones.append(zone_data)
        
        self.current_config['mine_zones'] = zones
        return self.save_config()
    
    def get_risk_thresholds(self):
        """Get risk level thresholds"""
        return self.current_config.get('risk_thresholds', {
            'low': 0.3,
            'medium': 0.7,
            'high': 0.85
        })
    
    def update_risk_thresholds(self, thresholds):
        """Update risk level thresholds"""
        current_thresholds = self.get_risk_thresholds()
        current_thresholds.update(thresholds)
        self.current_config['risk_thresholds'] = current_thresholds
        return self.save_config()
    
    def get_notification_settings(self):
        """Get notification settings"""
        return self.current_config.get('notification_settings', {})
    
    def update_notification_settings(self, settings):
        """Update notification settings"""
        current_settings = self.get_notification_settings()
        current_settings.update(settings)
        self.current_config['notification_settings'] = current_settings
        return self.save_config()
    
    def get_api_settings(self):
        """Get API configuration settings"""
        return {
            'openai_configured': os.getenv('OPENAI_API_KEY') is not None,
            'twilio_configured': all([
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN'),
                os.getenv('TWILIO_PHONE_NUMBER')
            ]),
            'sendgrid_configured': os.getenv('SENDGRID_API_KEY') is not None
        }
    
    def export_config(self, filename=None):
        """Export configuration to a file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'mine_config_backup_{timestamp}.json'
        
        try:
            export_data = {
                'config': self.current_config,
                'export_timestamp': datetime.now().isoformat(),
                'system_info': {
                    'api_settings': self.get_api_settings(),
                    'version': '1.0.0'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return {'success': True, 'filename': filename}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_config(self, filename):
        """Import configuration from a file"""
        try:
            with open(filename, 'r') as f:
                import_data = json.load(f)
            
            if 'config' in import_data:
                imported_config = import_data['config']
                # Validate imported config has required fields
                if self._validate_config(imported_config):
                    self.current_config = {**self.default_config, **imported_config}
                    return self.save_config()
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def _validate_config(self, config):
        """Validate configuration structure"""
        required_keys = ['mine_name', 'coordinates', 'sensor_count']
        return all(key in config for key in required_keys)
    
    def get_system_health(self):
        """Get system health indicators based on configuration"""
        health = {
            'config_status': 'healthy',
            'api_connectivity': {},
            'settings_completeness': 0,
            'recommendations': []
        }
        
        # Check API configurations
        api_settings = self.get_api_settings()
        health['api_connectivity'] = api_settings
        
        # Calculate settings completeness
        total_settings = len(self.default_config)
        configured_settings = len([k for k, v in self.current_config.items() if v is not None and v != ''])
        health['settings_completeness'] = (configured_settings / total_settings) * 100
        
        # Generate recommendations
        if not api_settings['openai_configured']:
            health['recommendations'].append('Configure OpenAI API key for advanced AI analysis')
        
        if not api_settings['twilio_configured']:
            health['recommendations'].append('Configure Twilio for SMS alerts')
        
        if not api_settings['sendgrid_configured']:
            health['recommendations'].append('Configure SendGrid for email notifications')
        
        if self.current_config.get('sensor_count', 0) < 20:
            health['recommendations'].append('Consider deploying more sensors for better coverage')
        
        return health
