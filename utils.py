import psutil
import os
import socket
import time
import threading
import logging
from datetime import datetime, timedelta
import json
import hashlib
import random
import numpy as np

class Utils:
    def __init__(self):
        self.start_time = datetime.now()
        self.error_log = []
        self.performance_metrics = []
        self.system_alerts = []
        
        # Setup logging
        self._setup_logging()
        
        # Start background monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._background_system_monitor, daemon=True)
        self.monitor_thread.start()
    
    def _setup_logging(self):
        """Setup application logging"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/mine_monitoring.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('MineMonitoring')
    
    def get_system_health(self):
        """Get comprehensive system health metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network status
            network_status = self._check_network_connectivity()
            
            # System uptime
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            # Error count in last hour
            recent_errors = len([e for e in self.error_log 
                               if e['timestamp'] > datetime.now() - timedelta(hours=1)])
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_status': network_status,
                'uptime_hours': uptime_hours,
                'error_count': recent_errors,
                'active_processes': len(psutil.pids()),
                'load_average': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
            }
            
        except Exception as e:
            self.log_error(f"Error getting system health: {e}")
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'network_status': 'Unknown',
                'uptime_hours': 0,
                'error_count': 0,
                'active_processes': 0,
                'load_average': 0
            }
    
    def _check_network_connectivity(self):
        """Check network connectivity"""
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return "Connected"
        except OSError:
            try:
                # Try local network
                socket.create_connection(("192.168.1.1", 80), timeout=3)
                return "Local Network Only"
            except OSError:
                return "Disconnected"
    
    def log_error(self, error_message, error_type="General", context=None):
        """Log application errors"""
        error_entry = {
            'timestamp': datetime.now(),
            'type': error_type,
            'message': str(error_message),
            'context': context,
            'id': hashlib.md5(f"{datetime.now()}{error_message}".encode()).hexdigest()[:8]
        }
        
        self.error_log.append(error_entry)
        
        # Keep only last 1000 errors
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-1000:]
        
        # Log to file
        self.logger.error(f"{error_type}: {error_message}")
        
        # Create system alert for critical errors
        if error_type in ['Critical', 'Database', 'Communication']:
            self._create_system_alert(error_message, error_type)
    
    def _create_system_alert(self, message, alert_type):
        """Create system-level alerts"""
        alert = {
            'id': hashlib.md5(f"{datetime.now()}{message}".encode()).hexdigest()[:8],
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'status': 'Active',
            'severity': 'High' if alert_type == 'Critical' else 'Medium'
        }
        
        self.system_alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.system_alerts) > 100:
            self.system_alerts = self.system_alerts[-100:]
    
    def get_performance_metrics(self, hours=24):
        """Get system performance metrics for specified period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [m for m in self.performance_metrics 
                         if m['timestamp'] > cutoff_time]
        
        if not recent_metrics:
            return {
                'avg_cpu': 0,
                'avg_memory': 0,
                'avg_response_time': 0,
                'total_requests': 0,
                'error_rate': 0
            }
        
        avg_cpu = np.mean([m['cpu_usage'] for m in recent_metrics])
        avg_memory = np.mean([m['memory_usage'] for m in recent_metrics])
        avg_response_time = np.mean([m.get('response_time', 0) for m in recent_metrics])
        total_requests = sum([m.get('requests', 0) for m in recent_metrics])
        total_errors = sum([m.get('errors', 0) for m in recent_metrics])
        error_rate = (total_errors / max(total_requests, 1)) * 100
        
        return {
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'avg_response_time': avg_response_time,
            'total_requests': total_requests,
            'error_rate': error_rate
        }
    
    def validate_sensor_data(self, sensor_data):
        """Validate incoming sensor data"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['timestamp', 'location']
        for field in required_fields:
            if field not in sensor_data:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False
        
        # Validate data ranges
        if 'temperature' in sensor_data:
            temp = sensor_data['temperature']
            if temp < -50 or temp > 70:
                validation_results['warnings'].append(f"Temperature {temp}°C is outside normal range (-50 to 70°C)")
        
        if 'humidity' in sensor_data:
            humidity = sensor_data['humidity']
            if humidity < 0 or humidity > 100:
                validation_results['errors'].append(f"Humidity {humidity}% is outside valid range (0-100%)")
                validation_results['valid'] = False
        
        if 'rainfall_24h' in sensor_data:
            rainfall = sensor_data['rainfall_24h']
            if rainfall < 0:
                validation_results['errors'].append(f"Rainfall cannot be negative: {rainfall}")
                validation_results['valid'] = False
            elif rainfall > 500:
                validation_results['warnings'].append(f"Extremely high rainfall: {rainfall}mm")
        
        # Validate displacement readings
        if 'displacement_readings' in sensor_data:
            displacements = sensor_data['displacement_readings']
            for i, displacement in enumerate(displacements):
                if abs(displacement) > 100:  # 100mm threshold
                    validation_results['warnings'].append(f"High displacement reading at sensor {i}: {displacement}mm")
        
        # Validate strain readings
        if 'strain_readings' in sensor_data:
            strains = sensor_data['strain_readings']
            for i, strain in enumerate(strains):
                if strain < 0 or strain > 10000:  # microstrain limits
                    validation_results['warnings'].append(f"Unusual strain reading at sensor {i}: {strain} microstrain")
        
        # Validate timestamp
        if 'timestamp' in sensor_data:
            timestamp = sensor_data['timestamp']
            if isinstance(timestamp, datetime):
                # Check if timestamp is too far in the future or past
                now = datetime.now()
                if timestamp > now + timedelta(minutes=5):
                    validation_results['warnings'].append("Timestamp is in the future")
                elif timestamp < now - timedelta(days=1):
                    validation_results['warnings'].append("Timestamp is more than 1 day old")
        
        return validation_results
    
    def calculate_data_quality_score(self, sensor_data):
        """Calculate data quality score for sensor readings"""
        score = 100
        
        # Check completeness
        expected_fields = ['temperature', 'humidity', 'rainfall_24h', 'displacement_readings', 
                          'strain_readings', 'pore_pressure', 'vibration_amplitude']
        missing_fields = sum(1 for field in expected_fields if field not in sensor_data)
        score -= (missing_fields / len(expected_fields)) * 20
        
        # Check data freshness
        if 'timestamp' in sensor_data:
            age_hours = (datetime.now() - sensor_data['timestamp']).total_seconds() / 3600
            if age_hours > 24:
                score -= 30
            elif age_hours > 6:
                score -= 15
            elif age_hours > 1:
                score -= 5
        
        # Check for outliers
        validation = self.validate_sensor_data(sensor_data)
        if validation['errors']:
            score -= len(validation['errors']) * 15
        if validation['warnings']:
            score -= len(validation['warnings']) * 5
        
        # Check sensor status
        active_sensors = sensor_data.get('active_sensors', 0)
        total_sensors = 50  # Assuming 50 total sensors
        sensor_availability = (active_sensors / total_sensors) * 100
        if sensor_availability < 80:
            score -= (80 - sensor_availability) * 0.5
        
        return max(0, min(100, score))
    
    def generate_data_integrity_hash(self, data):
        """Generate hash for data integrity verification"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def verify_data_integrity(self, data, expected_hash):
        """Verify data integrity using hash comparison"""
        actual_hash = self.generate_data_integrity_hash(data)
        return actual_hash == expected_hash
    
    def format_duration(self, seconds):
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"
    
    def format_file_size(self, bytes_size):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates (Haversine formula)"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = (np.sin(delta_lat/2) * np.sin(delta_lat/2) +
             np.cos(lat1_rad) * np.cos(lat2_rad) *
             np.sin(delta_lon/2) * np.sin(delta_lon/2))
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def is_within_mine_boundary(self, lat, lon, mine_boundaries):
        """Check if coordinates are within mine boundaries"""
        # Simple polygon containment check
        x, y = lon, lat
        n = len(mine_boundaries)
        inside = False
        
        p1x, p1y = mine_boundaries[0]
        for i in range(1, n + 1):
            p2x, p2y = mine_boundaries[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def generate_alert_id(self, location, severity, timestamp=None):
        """Generate unique alert ID"""
        if timestamp is None:
            timestamp = datetime.now()
        
        source_string = f"{location}_{severity}_{timestamp.isoformat()}"
        return hashlib.md5(source_string.encode()).hexdigest()[:8].upper()
    
    def sanitize_input(self, input_string, max_length=255):
        """Sanitize user input for security"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Remove potentially dangerous characters
        sanitized = input_string.strip()
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    def export_system_report(self, include_sensitive=False):
        """Export comprehensive system report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'system_health': self.get_system_health(),
            'performance_metrics': self.get_performance_metrics(),
            'error_summary': {
                'total_errors': len(self.error_log),
                'recent_errors': len([e for e in self.error_log 
                                    if e['timestamp'] > datetime.now() - timedelta(hours=24)]),
                'error_types': {}
            },
            'uptime': self.format_duration((datetime.now() - self.start_time).total_seconds()),
            'configuration': {
                'monitoring_active': self.monitoring_active,
                'log_level': self.logger.level
            }
        }
        
        # Error type breakdown
        for error in self.error_log:
            error_type = error['type']
            report['error_summary']['error_types'][error_type] = \
                report['error_summary']['error_types'].get(error_type, 0) + 1
        
        # Include sensitive information if requested
        if include_sensitive:
            report['recent_errors'] = [
                {
                    'timestamp': e['timestamp'].isoformat(),
                    'type': e['type'],
                    'message': e['message']
                }
                for e in self.error_log[-10:]  # Last 10 errors
            ]
        
        return report
    
    def _background_system_monitor(self):
        """Background system monitoring"""
        while self.monitoring_active:
            try:
                # Collect performance metrics
                health_data = self.get_system_health()
                
                metric_entry = {
                    'timestamp': datetime.now(),
                    'cpu_usage': health_data['cpu_usage'],
                    'memory_usage': health_data['memory_usage'],
                    'disk_usage': health_data['disk_usage'],
                    'network_status': health_data['network_status'],
                    'error_count': health_data['error_count']
                }
                
                self.performance_metrics.append(metric_entry)
                
                # Keep only last 24 hours of metrics
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.performance_metrics = [
                    m for m in self.performance_metrics 
                    if m['timestamp'] > cutoff_time
                ]
                
                # Check for system alerts
                if health_data['cpu_usage'] > 90:
                    self._create_system_alert("High CPU usage detected", "Performance")
                
                if health_data['memory_usage'] > 90:
                    self._create_system_alert("High memory usage detected", "Performance")
                
                if health_data['disk_usage'] > 95:
                    self._create_system_alert("Disk space critically low", "Storage")
                
                if health_data['network_status'] == "Disconnected":
                    self._create_system_alert("Network connectivity lost", "Network")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.log_error(f"Background monitoring error: {e}", "Monitor")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def get_system_alerts(self):
        """Get active system alerts"""
        return [alert for alert in self.system_alerts if alert['status'] == 'Active']
    
    def resolve_system_alert(self, alert_id):
        """Resolve a system alert"""
        for alert in self.system_alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'Resolved'
                alert['resolved_at'] = datetime.now()
                return True
        return False
    
    def get_error_log(self, hours=24, error_type=None):
        """Get filtered error log"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_errors = [
            e for e in self.error_log 
            if e['timestamp'] > cutoff_time
        ]
        
        if error_type:
            filtered_errors = [
                e for e in filtered_errors 
                if e['type'] == error_type
            ]
        
        return sorted(filtered_errors, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_resources(self):
        """Cleanup system resources"""
        # Clear old logs
        cutoff_time = datetime.now() - timedelta(days=30)
        self.error_log = [e for e in self.error_log if e['timestamp'] > cutoff_time]
        self.performance_metrics = [m for m in self.performance_metrics if m['timestamp'] > cutoff_time]
        
        # Clear resolved alerts
        self.system_alerts = [a for a in self.system_alerts if a['status'] == 'Active']
        
        # Log cleanup
        self.logger.info("System resources cleaned up")
    
    def shutdown(self):
        """Shutdown utilities"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        # Final cleanup
        self.cleanup_resources()
        self.logger.info("Utils system shutdown complete")
