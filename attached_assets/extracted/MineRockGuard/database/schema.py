"""
Database schema for the Rockfall Prediction System
Manages sensor data, alerts, mine sites, and historical analysis
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

Base = declarative_base()

class MineSite(Base):
    """Mining site information"""
    __tablename__ = 'mine_sites'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    coordinates = Column(JSON)  # {"lat": float, "lon": float}
    site_boundaries = Column(JSON)  # Polygon coordinates
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="mine_site")
    alerts = relationship("Alert", back_populates="mine_site")
    risk_assessments = relationship("RiskAssessment", back_populates="mine_site")

class Sensor(Base):
    """IoT sensor information and metadata"""
    __tablename__ = 'sensors'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(50), unique=True, nullable=False)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # displacement, strain, pressure, etc.
    coordinates = Column(JSON)  # {"x": float, "y": float, "z": float}
    installation_date = Column(DateTime, default=func.now())
    last_maintenance = Column(DateTime)
    status = Column(String(20), default='active')  # active, inactive, maintenance
    calibration_data = Column(JSON)
    communication_protocol = Column(String(30))  # LoRaWAN, MQTT, HTTP, etc.
    battery_level = Column(Float)
    signal_strength = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")

class SensorReading(Base):
    """Individual sensor data readings"""
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('sensors.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    quality_score = Column(Float, default=1.0)  # Data quality indicator
    processed = Column(Boolean, default=False)
    anomaly_detected = Column(Boolean, default=False)
    sensor_metadata = Column(JSON)  # Additional sensor-specific data
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")

class EnvironmentalData(Base):
    """Environmental conditions affecting rockfall risk"""
    __tablename__ = 'environmental_data'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    precipitation = Column(Float)
    atmospheric_pressure = Column(Float)
    seismic_activity = Column(Float)
    source = Column(String(50))  # weather_api, local_station, etc.

class RiskAssessment(Base):
    """ML-generated risk assessments"""
    __tablename__ = 'risk_assessments'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_score = Column(Float, nullable=False)  # 0-100
    affected_zones = Column(JSON)  # List of zone coordinates
    contributing_factors = Column(JSON)  # Factors that influenced the prediction
    model_version = Column(String(20))
    confidence_score = Column(Float)
    predicted_timeframe = Column(String(50))  # "next_24h", "next_week", etc.
    recommendations = Column(Text)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="risk_assessments")

class Alert(Base):
    """Alert and notification records"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # rockfall_warning, sensor_failure, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    location = Column(JSON)  # Specific coordinates if applicable
    triggered_by = Column(String(100))  # sensor_id or system component
    timestamp = Column(DateTime, default=func.now())
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    actions_taken = Column(Text)
    
    # Notification channels used
    sms_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    siren_activated = Column(Boolean, default=False)
    radio_broadcast = Column(Boolean, default=False)
    
    # Relationships
    mine_site = relationship("MineSite", back_populates="alerts")

class DroneImagery(Base):
    """Drone imagery and analysis data"""
    __tablename__ = 'drone_imagery'
    
    id = Column(Integer, primary_key=True)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'), nullable=False)
    flight_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    image_path = Column(String(500))  # File system path or cloud URL
    coordinates = Column(JSON)  # GPS coordinates where image was taken
    altitude = Column(Float)
    camera_angle = Column(Float)
    weather_conditions = Column(String(100))
    
    # AI Analysis results
    processed = Column(Boolean, default=False)
    cracks_detected = Column(Integer, default=0)
    crack_analysis = Column(JSON)  # Detailed crack analysis
    slope_stability_score = Column(Float)
    anomalies_detected = Column(JSON)
    change_detection = Column(JSON)  # Comparison with previous images
    
    analysis_model_version = Column(String(20))
    processing_timestamp = Column(DateTime)

class SystemLog(Base):
    """System operation and maintenance logs"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component = Column(String(50), nullable=False)  # sensor_manager, ml_engine, etc.
    message = Column(Text, nullable=False)
    details = Column(JSON)  # Additional structured data
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))
    user_id = Column(String(50))

class CommunicationLog(Base):
    """Communication system logs (LoRaWAN, radio, etc.)"""
    __tablename__ = 'communication_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    protocol = Column(String(30), nullable=False)  # LoRaWAN, radio, MQTT, etc.
    direction = Column(String(10), nullable=False)  # inbound, outbound
    source = Column(String(100))
    destination = Column(String(100))
    message_type = Column(String(50))
    payload = Column(Text)
    signal_strength = Column(Float)
    success = Column(Boolean, default=True)
    error_details = Column(Text)
    mine_site_id = Column(Integer, ForeignKey('mine_sites.id'))

# Database connection and session management
class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not found")
        
        self.engine = create_engine(self.database_url)
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

# Global database manager instance
db_manager = DatabaseManager()