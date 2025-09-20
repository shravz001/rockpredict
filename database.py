import sqlite3
import json
import os
import threading
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="mine_monitoring.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
        
        # Start background maintenance
        self.maintenance_active = True
        self.maintenance_thread = threading.Thread(target=self._background_maintenance, daemon=True)
        self.maintenance_thread.start()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sensor data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    location_x REAL,
                    location_y REAL,
                    location_z REAL,
                    value REAL NOT NULL,
                    unit TEXT,
                    status TEXT DEFAULT 'Online',
                    battery_level INTEGER,
                    signal_strength INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Environmental data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS environmental_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    rainfall_24h REAL,
                    wind_speed REAL,
                    atmospheric_pressure REAL,
                    soil_moisture REAL,
                    location TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    location TEXT NOT NULL,
                    risk_level REAL NOT NULL,
                    risk_class INTEGER NOT NULL,
                    confidence_score REAL,
                    model_version TEXT,
                    features_json TEXT,
                    prediction_horizon INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT,
                    action_required TEXT,
                    timestamp DATETIME NOT NULL,
                    status TEXT DEFAULT 'Active',
                    source TEXT,
                    acknowledged_by TEXT,
                    acknowledged_at DATETIME,
                    resolved_by TEXT,
                    resolved_at DATETIME,
                    escalation_level INTEGER DEFAULT 0,
                    escalation_deadline DATETIME,
                    notifications_sent TEXT,
                    resolution_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Communication log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS communication_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    comm_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    recipient TEXT,
                    message TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    metadata_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # System health table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_status TEXT,
                    active_sensors INTEGER,
                    database_size_mb REAL,
                    uptime_hours REAL,
                    error_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # DEM (Digital Elevation Model) data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dem_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grid_x INTEGER NOT NULL,
                    grid_y INTEGER NOT NULL,
                    elevation REAL NOT NULL,
                    slope_angle REAL,
                    slope_aspect REAL,
                    geological_type TEXT,
                    stability_factor REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Drone imagery analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drone_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    flight_id TEXT,
                    image_path TEXT,
                    analysis_type TEXT,
                    features_detected TEXT,
                    confidence_scores TEXT,
                    anomalies_found INTEGER DEFAULT 0,
                    location_x REAL,
                    location_y REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor_id ON sensor_data(sensor_id)",
                "CREATE INDEX IF NOT EXISTS idx_environmental_data_timestamp ON environmental_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_risk_predictions_timestamp ON risk_predictions(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_risk_predictions_location ON risk_predictions(location)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)",
                "CREATE INDEX IF NOT EXISTS idx_communication_log_timestamp ON communication_log(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_dem_data_grid ON dem_data(grid_x, grid_y)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
    
    def store_sensor_data(self, sensor_data):
        """Store sensor readings in the database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    timestamp = sensor_data.get('timestamp', datetime.now())
                    
                    # Store displacement sensor data
                    if 'displacement_readings' in sensor_data:
                        for i, reading in enumerate(sensor_data['displacement_readings']):
                            cursor.execute('''
                                INSERT INTO sensor_data 
                                (timestamp, sensor_id, sensor_type, value, unit, location_x, location_y, location_z)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                timestamp,
                                f'DISP_{i+1:03d}',
                                'displacement',
                                reading,
                                'mm',
                                sensor_data.get('gps_lat', 0) + np.random.uniform(-0.001, 0.001),
                                sensor_data.get('gps_lon', 0) + np.random.uniform(-0.001, 0.001),
                                np.random.uniform(0, 200)
                            ))
                    
                    # Store strain sensor data
                    if 'strain_readings' in sensor_data:
                        for i, reading in enumerate(sensor_data['strain_readings']):
                            cursor.execute('''
                                INSERT INTO sensor_data 
                                (timestamp, sensor_id, sensor_type, value, unit, location_x, location_y, location_z)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                timestamp,
                                f'STRAIN_{i+1:03d}',
                                'strain',
                                reading,
                                'microstrain',
                                sensor_data.get('gps_lat', 0) + np.random.uniform(-0.001, 0.001),
                                sensor_data.get('gps_lon', 0) + np.random.uniform(-0.001, 0.001),
                                np.random.uniform(0, 200)
                            ))
                    
                    # Store pore pressure data
                    if 'pore_pressure' in sensor_data:
                        for i, reading in enumerate(sensor_data['pore_pressure']):
                            cursor.execute('''
                                INSERT INTO sensor_data 
                                (timestamp, sensor_id, sensor_type, value, unit, location_x, location_y, location_z)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                timestamp,
                                f'PORE_{i+1:03d}',
                                'pore_pressure',
                                reading,
                                'kPa',
                                sensor_data.get('gps_lat', 0) + np.random.uniform(-0.001, 0.001),
                                sensor_data.get('gps_lon', 0) + np.random.uniform(-0.001, 0.001),
                                np.random.uniform(0, 200)
                            ))
                    
                    # Store vibration data
                    if 'vibration_amplitude' in sensor_data:
                        cursor.execute('''
                            INSERT INTO sensor_data 
                            (timestamp, sensor_id, sensor_type, value, unit, location_x, location_y, location_z)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            timestamp,
                            'VIB_001',
                            'vibration',
                            sensor_data['vibration_amplitude'],
                            'mm/s',
                            sensor_data.get('gps_lat', 0),
                            sensor_data.get('gps_lon', 0),
                            100
                        ))
                    
                    # Store environmental data
                    cursor.execute('''
                        INSERT INTO environmental_data 
                        (timestamp, temperature, humidity, rainfall_24h, wind_speed, location)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        sensor_data.get('temperature'),
                        sensor_data.get('humidity'),
                        sensor_data.get('rainfall_24h'),
                        sensor_data.get('wind_speed'),
                        sensor_data.get('location', 'Unknown')
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error storing sensor data: {e}")
            return False
    
    def store_risk_prediction(self, location, risk_level, risk_class, confidence_score, features, model_version="1.0"):
        """Store risk prediction in the database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO risk_predictions 
                        (timestamp, location, risk_level, risk_class, confidence_score, 
                         model_version, features_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now(),
                        location,
                        risk_level,
                        risk_class,
                        confidence_score,
                        model_version,
                        json.dumps(features) if features else None
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error storing risk prediction: {e}")
            return False
    
    def store_alert(self, alert_data):
        """Store alert in the database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO alerts 
                        (id, title, severity, location, description, action_required, 
                         timestamp, status, source, escalation_level, escalation_deadline,
                         notifications_sent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_data['id'],
                        alert_data['title'],
                        alert_data['severity'],
                        alert_data['location'],
                        alert_data['description'],
                        alert_data['action'],
                        alert_data['timestamp'],
                        alert_data['status'],
                        alert_data['source'],
                        alert_data.get('escalation_level', 0),
                        alert_data.get('escalation_deadline'),
                        json.dumps(alert_data.get('notifications_sent', []))
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error storing alert: {e}")
            return False
    
    def update_alert_status(self, alert_id, status, updated_by=None, notes=None):
        """Update alert status in the database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    update_fields = []
                    values = []
                    
                    update_fields.append("status = ?")
                    values.append(status)
                    
                    if status == 'Acknowledged':
                        update_fields.extend(["acknowledged_by = ?", "acknowledged_at = ?"])
                        values.extend([updated_by, datetime.now()])
                    elif status == 'Resolved':
                        update_fields.extend(["resolved_by = ?", "resolved_at = ?"])
                        values.extend([updated_by, datetime.now()])
                        if notes:
                            update_fields.append("resolution_notes = ?")
                            values.append(notes)
                    
                    values.append(alert_id)
                    
                    cursor.execute(f'''
                        UPDATE alerts 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    ''', values)
                    
                    conn.commit()
                    return cursor.rowcount > 0
                    
        except Exception as e:
            print(f"Error updating alert status: {e}")
            return False
    
    def log_communication(self, log_entry):
        """Log communication event"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO communication_log 
                        (timestamp, comm_type, direction, recipient, message, status, 
                         error_message, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log_entry.get('timestamp', datetime.now()),
                        log_entry['type'],
                        log_entry['direction'],
                        log_entry.get('recipient'),
                        log_entry.get('message'),
                        log_entry['status'],
                        log_entry.get('error'),
                        json.dumps({k: v for k, v in log_entry.items() 
                                  if k not in ['timestamp', 'type', 'direction', 'recipient', 'message', 'status', 'error']})
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error logging communication: {e}")
            return False
    
    def store_system_health(self, health_data):
        """Store system health metrics"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO system_health 
                        (timestamp, cpu_usage, memory_usage, disk_usage, network_status,
                         active_sensors, database_size_mb, uptime_hours, error_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now(),
                        health_data.get('cpu_usage'),
                        health_data.get('memory_usage'),
                        health_data.get('disk_usage'),
                        health_data.get('network_status'),
                        health_data.get('active_sensors'),
                        health_data.get('database_size_mb'),
                        health_data.get('uptime_hours'),
                        health_data.get('error_count', 0)
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error storing system health: {e}")
            return False
    
    def get_sensor_data(self, sensor_type=None, hours=24, limit=1000):
        """Retrieve sensor data from the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = '''
                    SELECT * FROM sensor_data 
                    WHERE timestamp > ?
                '''
                params = [datetime.now() - timedelta(hours=hours)]
                
                if sensor_type:
                    base_query += ' AND sensor_type = ?'
                    params.append(sensor_type)
                
                base_query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving sensor data: {e}")
            return []
    
    def get_risk_history(self, location=None, hours=24):
        """Get risk prediction history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = '''
                    SELECT * FROM risk_predictions 
                    WHERE timestamp > ?
                '''
                params = [datetime.now() - timedelta(hours=hours)]
                
                if location:
                    base_query += ' AND location = ?'
                    params.append(location)
                
                base_query += ' ORDER BY timestamp DESC'
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving risk history: {e}")
            return []
    
    def get_database_size(self):
        """Get database file size and record counts"""
        try:
            # Get file size
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # Get record counts
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                tables = ['sensor_data', 'environmental_data', 'risk_predictions', 
                         'alerts', 'communication_log', 'system_health']
                
                total_records = 0
                table_counts = {}
                
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                    total_records += count
                
                return {
                    'size_mb': size_mb,
                    'total_records': total_records,
                    'table_counts': table_counts
                }
                
        except Exception as e:
            print(f"Error getting database size: {e}")
            return {'size_mb': 0, 'total_records': 0, 'table_counts': {}}
    
    def get_record_counts(self):
        """Get total record count across all tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM sensor_data) +
                        (SELECT COUNT(*) FROM environmental_data) +
                        (SELECT COUNT(*) FROM risk_predictions) +
                        (SELECT COUNT(*) FROM alerts) +
                        (SELECT COUNT(*) FROM communication_log) +
                        (SELECT COUNT(*) FROM system_health) as total
                ''')
                
                total = cursor.fetchone()[0]
                return {'total': total}
                
        except Exception as e:
            print(f"Error getting record counts: {e}")
            return {'total': 0}
    
    def cleanup_old_data(self, days=90):
        """Clean up old data from the database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cutoff_date = datetime.now() - timedelta(days=days)
                    total_deleted = 0
                    
                    # Tables to clean up (keeping alerts and risk_predictions longer)
                    cleanup_tables = [
                        ('sensor_data', 'timestamp'),
                        ('environmental_data', 'timestamp'),
                        ('communication_log', 'timestamp'),
                        ('system_health', 'timestamp')
                    ]
                    
                    for table, timestamp_col in cleanup_tables:
                        cursor.execute(f'DELETE FROM {table} WHERE {timestamp_col} < ?', (cutoff_date,))
                        deleted = cursor.rowcount
                        total_deleted += deleted
                        print(f"Cleaned {deleted} records from {table}")
                    
                    # Clean resolved alerts older than specified days
                    cursor.execute('''
                        DELETE FROM alerts 
                        WHERE status = 'Resolved' AND resolved_at < ?
                    ''', (cutoff_date,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    print(f"Cleaned {deleted} resolved alerts")
                    
                    conn.commit()
                    
                    # Vacuum database to reclaim space
                    cursor.execute('VACUUM')
                    
                    return {'records_deleted': total_deleted}
                    
        except Exception as e:
            print(f"Error cleaning up database: {e}")
            return {'records_deleted': 0}
    
    def export_data(self, start_date=None, end_date=None, tables=None):
        """Export data to CSV files"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            if not tables:
                tables = ['sensor_data', 'environmental_data', 'risk_predictions', 'alerts']
            
            export_dir = f"exports_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(export_dir, exist_ok=True)
            
            exported_files = []
            
            with self.get_connection() as conn:
                for table in tables:
                    query = f'''
                        SELECT * FROM {table} 
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp
                    '''
                    
                    df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                    
                    if not df.empty:
                        filename = os.path.join(export_dir, f"{table}.csv")
                        df.to_csv(filename, index=False)
                        exported_files.append(filename)
            
            return {
                'filename': export_dir,
                'files_exported': exported_files,
                'record_count': len(exported_files)
            }
            
        except Exception as e:
            print(f"Error exporting data: {e}")
            return {'filename': None, 'files_exported': [], 'record_count': 0}
    
    def create_backup(self):
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"mine_monitoring_backup_{timestamp}.db"
            
            # Create backup directory if it doesn't exist
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Create backup using SQLite backup API
            with self.get_connection() as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            
            return {
                'filename': backup_path,
                'size_mb': os.path.getsize(backup_path) / (1024 * 1024),
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return {'filename': None, 'size_mb': 0, 'timestamp': None}
    
    def get_last_backup_info(self):
        """Get information about the last backup"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                return {'date': 'Never', 'size_mb': 0}
            
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
            if not backup_files:
                return {'date': 'Never', 'size_mb': 0}
            
            # Get the most recent backup
            backup_files.sort(reverse=True)
            latest_backup = backup_files[0]
            backup_path = os.path.join(backup_dir, latest_backup)
            
            # Extract timestamp from filename
            timestamp_str = latest_backup.replace('mine_monitoring_backup_', '').replace('.db', '')
            backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            return {
                'date': backup_date.strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': os.path.getsize(backup_path) / (1024 * 1024)
            }
            
        except Exception as e:
            print(f"Error getting backup info: {e}")
            return {'date': 'Error', 'size_mb': 0}
    
    def get_data_statistics(self, days=7):
        """Get data statistics for the dashboard"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Sensor data statistics
                cursor.execute('''
                    SELECT sensor_type, COUNT(*) as count, AVG(value) as avg_value
                    FROM sensor_data 
                    WHERE timestamp > ?
                    GROUP BY sensor_type
                ''', (cutoff_date,))
                sensor_stats = {row[0]: {'count': row[1], 'avg_value': row[2]} 
                              for row in cursor.fetchall()}
                
                # Alert statistics
                cursor.execute('''
                    SELECT severity, COUNT(*) as count
                    FROM alerts 
                    WHERE timestamp > ?
                    GROUP BY severity
                ''', (cutoff_date,))
                alert_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Risk level trends
                cursor.execute('''
                    SELECT DATE(timestamp) as date, AVG(risk_level) as avg_risk
                    FROM risk_predictions 
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (cutoff_date,))
                risk_trends = [(row[0], row[1]) for row in cursor.fetchall()]
                
                return {
                    'sensor_stats': sensor_stats,
                    'alert_stats': alert_stats,
                    'risk_trends': risk_trends
                }
                
        except Exception as e:
            print(f"Error getting data statistics: {e}")
            return {'sensor_stats': {}, 'alert_stats': {}, 'risk_trends': []}
    
    def _background_maintenance(self):
        """Background maintenance tasks"""
        while self.maintenance_active:
            try:
                # Run maintenance every 6 hours
                time.sleep(6 * 3600)
                
                # Clean up old temporary data
                self._cleanup_temp_data()
                
                # Optimize database
                self._optimize_database()
                
                # Store system health metrics
                from utils import Utils
                utils = Utils()
                health_data = utils.get_system_health()
                health_data['database_size_mb'] = self.get_database_size()['size_mb']
                self.store_system_health(health_data)
                
            except Exception as e:
                print(f"Background maintenance error: {e}")
                time.sleep(3600)  # Wait 1 hour before retrying
    
    def _cleanup_temp_data(self):
        """Clean up temporary and old data"""
        try:
            # Remove old sensor data beyond retention period
            cutoff_date = datetime.now() - timedelta(days=365)  # Keep 1 year
            
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        DELETE FROM sensor_data 
                        WHERE timestamp < ? AND sensor_type != 'critical'
                    ''', (cutoff_date,))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"Error cleaning temp data: {e}")
    
    def _optimize_database(self):
        """Optimize database performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Analyze tables for query optimization
                cursor.execute('ANALYZE')
                
                # Update statistics
                cursor.execute('PRAGMA optimize')
                
                conn.commit()
                
        except Exception as e:
            print(f"Error optimizing database: {e}")
    
    def shutdown(self):
        """Shutdown database manager"""
        self.maintenance_active = False
        if hasattr(self, 'maintenance_thread') and self.maintenance_thread.is_alive():
            self.maintenance_thread.join(timeout=10)
