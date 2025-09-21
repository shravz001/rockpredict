"""
Database management utilities for the Rockfall Prediction System
Handles initialization, data queries, and database operations
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from .schema import (
    DatabaseManager, MineSite, Sensor, SensorReading, 
    EnvironmentalData, RiskAssessment, Alert, DroneImagery, 
    SystemLog, CommunicationLog
)
import logging

logger = logging.getLogger(__name__)

class RockfallDatabaseManager:
    """High-level database operations for the rockfall prediction system"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default mine site and sensors if not exists"""
        session = self.db_manager.get_session()
        try:
            # Check if we have any mine sites
            mine_count = session.query(MineSite).count()
            
            if mine_count == 0:
                # Create default mine site
                default_mine = MineSite(
                    name="Copper Ridge Mine",
                    location="Colorado, USA",
                    coordinates={"lat": 39.7392, "lon": -104.9903},
                    site_boundaries=[
                        {"lat": 39.7400, "lon": -104.9910},
                        {"lat": 39.7400, "lon": -104.9890},
                        {"lat": 39.7380, "lon": -104.9890},
                        {"lat": 39.7380, "lon": -104.9910}
                    ],
                    active=True
                )
                session.add(default_mine)
                session.flush()
                
                # Create default sensors
                sensor_configs = [
                    {"type": "displacement", "coords": {"x": 100, "y": 200, "z": 50}},
                    {"type": "strain", "coords": {"x": 150, "y": 180, "z": 45}},
                    {"type": "pressure", "coords": {"x": 120, "y": 220, "z": 55}},
                    {"type": "vibration", "coords": {"x": 180, "y": 160, "z": 40}},
                    {"type": "tilt", "coords": {"x": 90, "y": 240, "z": 60}}
                ]
                
                for i, config in enumerate(sensor_configs):
                    sensor = Sensor(
                        sensor_id=f"SENSOR_{config['type'].upper()}_{i+1:03d}",
                        mine_site_id=default_mine.id,
                        sensor_type=config['type'],
                        coordinates=config['coords'],
                        status='active',
                        communication_protocol='LoRaWAN',
                        battery_level=85.0,
                        signal_strength=-65.0
                    )
                    session.add(sensor)
                
                session.commit()
                logger.info("Initialized default mine site and sensors")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error initializing default data: {e}")
        finally:
            self.db_manager.close_session(session)
    
    def get_mine_sites(self) -> List[Dict[str, Any]]:
        """Get all active mine sites"""
        session = self.db_manager.get_session()
        try:
            sites = session.query(MineSite).filter_by(active=True).all()
            return [
                {
                    "id": site.id,
                    "name": site.name,
                    "location": site.location,
                    "coordinates": site.coordinates,
                    "site_boundaries": site.site_boundaries,
                    "sensor_count": len(site.sensors),
                    "created_at": site.created_at.isoformat()
                }
                for site in sites
            ]
        finally:
            self.db_manager.close_session(session)
    
    def get_sensors_for_site(self, mine_site_id: int) -> List[Dict[str, Any]]:
        """Get all sensors for a specific mine site"""
        session = self.db_manager.get_session()
        try:
            sensors = session.query(Sensor).filter_by(
                mine_site_id=mine_site_id, 
                status='active'
            ).all()
            
            sensor_data = []
            for sensor in sensors:
                # Get latest reading
                latest_reading = session.query(SensorReading).filter_by(
                    sensor_id=sensor.id
                ).order_by(desc(SensorReading.timestamp)).first()
                
                sensor_data.append({
                    "id": sensor.id,
                    "sensor_id": sensor.sensor_id,
                    "sensor_type": sensor.sensor_type,
                    "coordinates": sensor.coordinates,
                    "status": sensor.status,
                    "communication_protocol": sensor.communication_protocol,
                    "battery_level": sensor.battery_level,
                    "signal_strength": sensor.signal_strength,
                    "latest_value": latest_reading.value if latest_reading else None,
                    "latest_timestamp": latest_reading.timestamp.isoformat() if latest_reading else None,
                    "installation_date": sensor.installation_date.isoformat() if sensor.installation_date is not None else None
                })
            
            return sensor_data
            
        finally:
            self.db_manager.close_session(session)
    
    def get_sensor_readings(self, sensor_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent sensor readings for a specific sensor"""
        session = self.db_manager.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff_time
            ).order_by(asc(SensorReading.timestamp)).all()
            
            return [
                {
                    "timestamp": reading.timestamp.isoformat(),
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality_score": reading.quality_score,
                    "anomaly_detected": reading.anomaly_detected
                }
                for reading in readings
            ]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_environmental_data(self, mine_site_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent environmental data for a mine site"""
        session = self.db_manager.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            env_data = session.query(EnvironmentalData).filter(
                EnvironmentalData.mine_site_id == mine_site_id,
                EnvironmentalData.timestamp >= cutoff_time
            ).order_by(asc(EnvironmentalData.timestamp)).all()
            
            return [
                {
                    "timestamp": data.timestamp.isoformat(),
                    "temperature": data.temperature,
                    "humidity": data.humidity,
                    "wind_speed": data.wind_speed,
                    "wind_direction": data.wind_direction,
                    "precipitation": data.precipitation,
                    "atmospheric_pressure": data.atmospheric_pressure,
                    "seismic_activity": data.seismic_activity,
                    "source": data.source
                }
                for data in env_data
            ]
            
        finally:
            self.db_manager.close_session(session)
    
    def store_risk_assessment(self, mine_site_id: int, risk_level: str, 
                            risk_score: float, affected_zones: List[Dict],
                            contributing_factors: Dict, model_version: str,
                            confidence_score: float, timeframe: str,
                            recommendations: str) -> int:
        """Store a new risk assessment"""
        session = self.db_manager.get_session()
        try:
            assessment = RiskAssessment(
                mine_site_id=mine_site_id,
                risk_level=risk_level,
                risk_score=risk_score,
                affected_zones=affected_zones,
                contributing_factors=contributing_factors,
                model_version=model_version,
                confidence_score=confidence_score,
                predicted_timeframe=timeframe,
                recommendations=recommendations
            )
            
            session.add(assessment)
            session.commit()
            session.refresh(assessment)
            return getattr(assessment, 'id')
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing risk assessment: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_recent_risk_assessments(self, mine_site_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent risk assessments for a mine site"""
        session = self.db_manager.get_session()
        try:
            assessments = session.query(RiskAssessment).filter_by(
                mine_site_id=mine_site_id
            ).order_by(desc(RiskAssessment.timestamp)).limit(limit).all()
            
            return [
                {
                    "id": assessment.id,
                    "timestamp": assessment.timestamp.isoformat(),
                    "risk_level": assessment.risk_level,
                    "risk_score": assessment.risk_score,
                    "affected_zones": assessment.affected_zones,
                    "contributing_factors": assessment.contributing_factors,
                    "confidence_score": assessment.confidence_score,
                    "predicted_timeframe": assessment.predicted_timeframe,
                    "recommendations": assessment.recommendations
                }
                for assessment in assessments
            ]
            
        finally:
            self.db_manager.close_session(session)
    
    def create_alert(self, mine_site_id: int, alert_type: str, severity: str,
                    title: str, message: str, location: Optional[Dict] = None,
                    triggered_by: Optional[str] = None) -> int:
        """Create a new alert"""
        session = self.db_manager.get_session()
        try:
            alert = Alert(
                mine_site_id=mine_site_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                location=location,
                triggered_by=triggered_by
            )
            
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return getattr(alert, 'id')
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_active_alerts(self, mine_site_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        session = self.db_manager.get_session()
        try:
            query = session.query(Alert).filter_by(resolved=False)
            
            if mine_site_id:
                query = query.filter_by(mine_site_id=mine_site_id)
            
            alerts = query.order_by(desc(Alert.timestamp)).all()
            
            return [
                {
                    "id": alert.id,
                    "mine_site_id": alert.mine_site_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "message": alert.message,
                    "location": alert.location,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged,
                    "acknowledged_by": alert.acknowledged_by,
                    "sms_sent": alert.sms_sent,
                    "email_sent": alert.email_sent,
                    "siren_activated": alert.siren_activated
                }
                for alert in alerts
            ]
            
        finally:
            self.db_manager.close_session(session)
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        session = self.db_manager.get_session()
        try:
            alert = session.query(Alert).get(alert_id)
            if alert:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error acknowledging alert: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def resolve_alert(self, alert_id: int, resolved_by: str, actions_taken: str) -> bool:
        """Resolve an alert"""
        session = self.db_manager.get_session()
        try:
            alert = session.query(Alert).get(alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_by = resolved_by
                alert.resolved_at = datetime.now()
                alert.actions_taken = actions_taken
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error resolving alert: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def get_system_statistics(self, mine_site_id: int) -> Dict[str, Any]:
        """Get system statistics for a mine site"""
        session = self.db_manager.get_session()
        try:
            # Sensor statistics
            total_sensors = session.query(Sensor).filter_by(
                mine_site_id=mine_site_id, status='active'
            ).count()
            
            # Recent readings count (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_readings = session.query(SensorReading).join(Sensor).filter(
                Sensor.mine_site_id == mine_site_id,
                SensorReading.timestamp >= cutoff_time
            ).count()
            
            # Active alerts
            active_alerts = session.query(Alert).filter_by(
                mine_site_id=mine_site_id, resolved=False
            ).count()
            
            # Latest risk assessment
            latest_risk = session.query(RiskAssessment).filter_by(
                mine_site_id=mine_site_id
            ).order_by(desc(RiskAssessment.timestamp)).first()
            
            # Communication statistics - simplified to avoid SQLAlchemy function issues
            comm_logs = session.query(CommunicationLog).filter(
                CommunicationLog.mine_site_id == mine_site_id,
                CommunicationLog.timestamp >= cutoff_time
            ).all()
            
            if comm_logs:
                successful_comms = sum(1 for log in comm_logs if bool(log.success))
                comm_success_rate = successful_comms / len(comm_logs)
            else:
                comm_success_rate = 0
            
            return {
                "total_sensors": total_sensors,
                "recent_readings": recent_readings,
                "active_alerts": active_alerts,
                "latest_risk_level": latest_risk.risk_level if latest_risk else "unknown",
                "latest_risk_score": latest_risk.risk_score if latest_risk else 0,
                "communication_success_rate": float(comm_success_rate),
                "system_uptime": "99.2%",  # This would come from system monitoring
                "last_updated": datetime.now().isoformat()
            }
            
        finally:
            self.db_manager.close_session(session)
    
    def get_historical_trends(self, mine_site_id: int, days: int = 30) -> Dict[str, Any]:
        """Get historical trends for risk analysis"""
        session = self.db_manager.get_session()
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # Risk score trends
            risk_assessments = session.query(RiskAssessment).filter(
                RiskAssessment.mine_site_id == mine_site_id,
                RiskAssessment.timestamp >= cutoff_time
            ).order_by(asc(RiskAssessment.timestamp)).all()
            
            # Alert frequency trends
            alerts_by_day = session.query(
                func.date(Alert.timestamp).label('date'),
                func.count(Alert.id).label('count')
            ).filter(
                Alert.mine_site_id == mine_site_id,
                Alert.timestamp >= cutoff_time
            ).group_by(func.date(Alert.timestamp)).all()
            
            return {
                "risk_trends": [
                    {
                        "timestamp": assessment.timestamp.isoformat(),
                        "risk_score": assessment.risk_score,
                        "risk_level": assessment.risk_level
                    }
                    for assessment in risk_assessments
                ],
                "alert_frequency": [
                    {
                        "date": alert_day.date.isoformat(),
                        "count": alert_day.count
                    }
                    for alert_day in alerts_by_day
                ]
            }
            
        finally:
            self.db_manager.close_session(session)

# Global database manager instance - initialize lazily
rockfall_db = None

def get_rockfall_db():
    """Get or create the global database manager instance"""
    global rockfall_db
    if rockfall_db is None:
        rockfall_db = RockfallDatabaseManager()
    return rockfall_db