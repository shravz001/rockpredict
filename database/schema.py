"""
Database schema definitions for the Rockfall Prediction System
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class MineSite(Base):
    __tablename__ = 'mine_sites'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    coordinates = Column(JSON)  # Store lat/lon as JSON
    site_boundaries = Column(JSON)  # Store boundary coordinates
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sensors = relationship("Sensor", back_populates="mine_site")
    environmental_data = relationship("EnvironmentalData", back_populates="mine_site")
    risk_assessments = relationship("RiskAssessment", back_populates="mine_site")
    alerts = relationship("Alert", back_populates="mine_site")

class Sensor(Base):
    __tablename__ = 'sensors'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(50), unique=True, nullable=False)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # displacement, strain, pressure, etc.
    coordinates = Column(JSON)  # x, y, z coordinates
    status = Column(String(20), default='active')  # active, inactive, maintenance
    communication_protocol = Column(String(50))  # LoRaWAN, radio, wired
    battery_level = Column(Float)
    signal_strength = Column(Float)
    installation_date = Column(DateTime)
    last_maintenance = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")

class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('sensors.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    quality_score = Column(Float)  # Data quality indicator
    anomaly_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")

class EnvironmentalData(Base):
    __tablename__ = 'environmental_data'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    precipitation = Column(Float)
    atmospheric_pressure = Column(Float)
    seismic_activity = Column(Float)
    source = Column(String(100))  # weather_station, satellite, manual
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="environmental_data")

class RiskAssessment(Base):
    __tablename__ = 'risk_assessments'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_score = Column(Float, nullable=False)
    affected_zones = Column(JSON)  # List of affected zone identifiers
    contributing_factors = Column(JSON)  # Key factors contributing to risk
    model_version = Column(String(50))
    confidence_score = Column(Float)
    predicted_timeframe = Column(String(100))  # Time window for prediction
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="risk_assessments")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # risk_threshold, sensor_failure, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    location = Column(JSON)  # Specific location within mine site
    timestamp = Column(DateTime, default=datetime.now)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    actions_taken = Column(Text)
    triggered_by = Column(String(100))  # sensor_id or system component
    sms_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    siren_activated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="alerts")

class DroneImagery(Base):
    __tablename__ = 'drone_imagery'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    flight_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    coverage_area = Column(JSON)  # Areas covered by this flight
    image_analysis = Column(JSON)  # Results of automated image analysis
    risk_indicators = Column(JSON)  # Risk factors detected in imagery
    storage_path = Column(String(500))  # Path to stored images
    analysis_status = Column(String(20), default='pending')  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    mine_site = relationship("MineSite")

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component = Column(String(100), nullable=False)  # Which system component
    message = Column(Text, nullable=False)
    details = Column(JSON)  # Additional structured details
    user_id = Column(String(100))
    session_id = Column(String(100))

class CommunicationLog(Base):
    __tablename__ = 'communication_logs'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))
    timestamp = Column(DateTime, default=datetime.now)
    communication_type = Column(String(50), nullable=False)  # SMS, email, LoRaWAN, radio
    recipient = Column(String(255))
    message_content = Column(Text)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    response_time = Column(Float)  # Response time in seconds
    gateway_used = Column(String(100))  # For LoRaWAN/radio communications

class DroneFlightLog(Base):
    __tablename__ = 'drone_flight_logs'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))
    drone_id = Column(String(50), nullable=False)
    mission_type = Column(String(50), nullable=False)  # patrol, emergency, inspection
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    flight_status = Column(String(20), nullable=False)  # grounded, flying, hovering, returning, completed
    battery_start = Column(Float)
    battery_end = Column(Float)
    weather_conditions = Column(String(100))
    flight_path = Column(JSON)  # Store flight path coordinates
    images_captured = Column(Integer, default=0)
    risk_alerts_generated = Column(Integer, default=0)
    total_flight_time = Column(Integer)  # Flight time in minutes

class DroneImageAnalysis(Base):
    __tablename__ = 'drone_image_analysis'
    
    id = Column(Integer, primary_key=True)
    flight_log_id = Column(Integer, ForeignKey('drone_flight_logs.id'))
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))
    timestamp = Column(DateTime, nullable=False)
    image_path = Column(String(500), nullable=False)
    capture_location = Column(JSON, nullable=False)  # lat, lon, altitude
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence = Column(Float)
    analysis_time_ms = Column(Integer)
    features_detected = Column(JSON)  # Array of detected geological features
    risk_indicators = Column(JSON)  # Detailed risk analysis data
    camera_settings = Column(JSON)  # Camera configuration used
    weather_conditions = Column(String(100))
    lighting_conditions = Column(String(50))
    image_quality = Column(String(20))
    processed = Column(Boolean, default=True)

class DroneAlert(Base):
    __tablename__ = 'drone_alerts'
    
    id = Column(Integer, primary_key=True)
    image_analysis_id = Column(Integer, ForeignKey('drone_image_analysis.id'))
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))
    drone_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    alert_type = Column(String(50), nullable=False)  # rockfall_risk, sensor_failure_backup, emergency
    risk_level = Column(String(20), nullable=False)
    location = Column(JSON, nullable=False)
    description = Column(Text)
    recommended_actions = Column(JSON)  # Array of recommended actions
    auto_generated = Column(Boolean, default=True)
    sensor_backup_mode = Column(Boolean, default=False)  # True if triggered by sensor failure
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    notification_sent = Column(Boolean, default=False)

class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            # Check for DATABASE_URL environment variable first (preferred for Replit/production)
            database_url = os.getenv('DATABASE_URL')
            
            if database_url is None:
                # Fallback to individual PostgreSQL environment variables
                db_host = os.getenv('PGHOST')
                db_port = os.getenv('PGPORT')
                db_name = os.getenv('PGDATABASE')
                db_user = os.getenv('PGUSER')
                db_password = os.getenv('PGPASSWORD')
                
                if all([db_host, db_port, db_name, db_user, db_password]):
                    database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
                else:
                    # Final fallback to SQLite for local development
                    db_path = os.getenv('DB_PATH', './data/rockfall_prediction.db')
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
                    database_url = f'sqlite:///{db_path}'
        
        try:
            self.engine = create_engine(database_url, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            print(f"Database connected: {database_url.split('://')[0].upper()}")
        except Exception as e:
            # Final fallback to simple SQLite
            print(f"Database connection failed, using fallback SQLite: {e}")
            fallback_path = './rockfall_prediction.db'
            self.engine = create_engine(f'sqlite:///{fallback_path}', echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close a database session"""
        session.close()
    
    def drop_tables(self):
        """Drop all database tables - USE WITH CAUTION"""
        Base.metadata.drop_all(bind=self.engine)