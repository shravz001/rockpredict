"""
Drone Integration Module
Integrates drone system with existing alert and monitoring infrastructure
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging

from communication.drone_system import DroneSystem
from database.database_manager import get_rockfall_db
from database.schema import DroneFlightLog, DroneImageAnalysis, DroneAlert, Alert
from alerts.notification_system import NotificationSystem

logger = logging.getLogger(__name__)

class DroneIntegration:
    """Integration layer between drone system and mine safety infrastructure"""
    
    def __init__(self):
        self.drone_system = DroneSystem()
        self.db_manager = get_rockfall_db()
        self.notification_system = NotificationSystem()
        self.sensor_failure_threshold = 3  # Number of failed sensors to trigger drone backup
        self.last_sensor_check = datetime.now()
        self.drone_backup_active = False
        
    def start_routine_patrol(self, mine_site_id: int = 1) -> Dict[str, Any]:
        """Start routine drone patrol mission"""
        try:
            # Log flight start in database
            flight_log = self._create_flight_log(mine_site_id, "patrol")
            
            # Start drone mission
            mission_result = self.drone_system.start_flight_mission("patrol")
            
            if mission_result["success"]:
                # Perform image captures along flight path
                self._execute_patrol_mission(flight_log.id, mine_site_id)
                
                return {
                    "success": True,
                    "message": "Routine patrol started successfully",
                    "flight_log_id": flight_log.id,
                    "estimated_completion": datetime.now() + timedelta(minutes=30)
                }
            else:
                return mission_result
                
        except Exception as e:
            logger.error(f"Failed to start routine patrol: {e}")
            return {"success": False, "message": str(e)}
    
    def _create_flight_log(self, mine_site_id: int, mission_type: str) -> DroneFlightLog:
        """Create flight log entry in database"""
        session = self.db_manager.db_manager.get_session()
        try:
            drone_status = self.drone_system.get_drone_status()
            
            flight_log = DroneFlightLog(
                mine_site_id=mine_site_id,
                drone_id=drone_status["drone_id"],
                mission_type=mission_type,
                start_time=datetime.now(),
                flight_status="flying",
                battery_start=drone_status["battery_level"],
                weather_conditions="clear",  # Would integrate with weather API
                flight_path=self.drone_system.flight_path
            )
            
            session.add(flight_log)
            session.commit()
            session.refresh(flight_log)
            return flight_log
            
        finally:
            self.db_manager.db_manager.close_session(session)
    
    def _execute_patrol_mission(self, flight_log_id: int, mine_site_id: int):
        """Execute patrol mission and process results"""
        images_captured = 0
        alerts_generated = 0
        
        # Capture images at each point in flight path
        for waypoint in self.drone_system.flight_path:
            if waypoint.get("capture_image", False):
                capture_result = self.drone_system.capture_and_analyze_image(waypoint)
                
                if capture_result["success"]:
                    images_captured += 1
                    
                    # Store analysis in database
                    analysis_id = self._store_image_analysis(
                        flight_log_id, mine_site_id, capture_result["result"]
                    )
                    
                    # Check if alert should be generated
                    if capture_result["risk_detected"]:
                        alert_generated = self._generate_drone_alert(
                            analysis_id, mine_site_id, capture_result["result"]
                        )
                        if alert_generated:
                            alerts_generated += 1
        
        # Update flight log with results
        self._update_flight_log(flight_log_id, images_captured, alerts_generated)
    
    def _store_image_analysis(self, flight_log_id: int, mine_site_id: int, 
                            analysis_result: Dict[str, Any]) -> int:
        """Store drone image analysis results in database"""
        session = self.db_manager.db_manager.get_session()
        try:
            image_analysis = DroneImageAnalysis(
                flight_log_id=flight_log_id,
                mine_site_id=mine_site_id,
                timestamp=datetime.fromisoformat(analysis_result["timestamp"]),
                image_path=analysis_result["image_path"],
                capture_location=analysis_result["location"],
                risk_score=analysis_result["analysis"]["risk_score"],
                risk_level=analysis_result["analysis"]["risk_level"],
                confidence=analysis_result["analysis"]["confidence"],
                analysis_time_ms=analysis_result["analysis"]["analysis_time_ms"],
                features_detected=analysis_result["analysis"]["features_detected"],
                risk_indicators=analysis_result["analysis"]["indicators"],
                camera_settings=analysis_result["camera_settings"],
                weather_conditions=analysis_result["analysis"]["weather_conditions"],
                lighting_conditions=analysis_result["analysis"]["lighting_conditions"],
                image_quality=analysis_result["analysis"]["image_quality"]
            )
            
            session.add(image_analysis)
            session.commit()
            session.refresh(image_analysis)
            return image_analysis.id
            
        finally:
            self.db_manager.db_manager.close_session(session)
    
    def _generate_drone_alert(self, analysis_id: int, mine_site_id: int, 
                            analysis_result: Dict[str, Any]) -> bool:
        """Generate alert based on drone analysis results"""
        try:
            analysis = analysis_result["analysis"]
            
            # Determine if alert should be generated
            if analysis["risk_level"] in ["high", "critical"]:
                session = self.db_manager.db_manager.get_session()
                try:
                    # Create drone-specific alert
                    drone_alert = DroneAlert(
                        image_analysis_id=analysis_id,
                        mine_site_id=mine_site_id,
                        drone_id=analysis_result["drone_id"],
                        timestamp=datetime.fromisoformat(analysis_result["timestamp"]),
                        alert_type="rockfall_risk",
                        risk_level=analysis["risk_level"],
                        location=analysis_result["location"],
                        description=f"Drone detected {analysis['risk_level']} rockfall risk. "
                                  f"Features detected: {', '.join(analysis['features_detected'])}",
                        recommended_actions=[
                            "Immediate area inspection required",
                            "Consider evacuation of nearby personnel",
                            "Deploy additional sensors if available",
                            "Monitor area with increased frequency"
                        ],
                        sensor_backup_mode=self.drone_backup_active
                    )
                    
                    session.add(drone_alert)
                    session.commit()
                    
                    # Send notifications
                    self._send_drone_alert_notifications(drone_alert, analysis)
                    
                    return True
                    
                finally:
                    self.db_manager.db_manager.close_session(session)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to generate drone alert: {e}")
            return False
    
    def _send_drone_alert_notifications(self, drone_alert: DroneAlert, analysis: Dict[str, Any]):
        """Send notifications for drone-detected risks"""
        try:
            # Prepare notification message
            message = f"""
DRONE ALERT - {drone_alert.risk_level.upper()} RISK DETECTED

Location: Lat {drone_alert.location['lat']:.6f}, Lon {drone_alert.location['lon']:.6f}
Risk Score: {analysis['risk_score']:.1f}/100
Confidence: {analysis['confidence']:.1%}
Features: {', '.join(analysis['features_detected'])}

{"⚠️ SENSOR BACKUP MODE ACTIVE ⚠️" if drone_alert.sensor_backup_mode else ""}

Immediate inspection recommended.
"""
            
            # Send notifications through existing system
            notification_result = self.notification_system.send_alert_notification(
                alert_type="drone_risk_detection",
                risk_level=drone_alert.risk_level,
                message=message,
                location=drone_alert.location
            )
            
            # Update alert with notification status
            if notification_result.get("success", False):
                session = self.db_manager.db_manager.get_session()
                try:
                    drone_alert.notification_sent = True
                    session.commit()
                finally:
                    self.db_manager.db_manager.close_session(session)
            
        except Exception as e:
            logger.error(f"Failed to send drone alert notifications: {e}")
    
    def _update_flight_log(self, flight_log_id: int, images_captured: int, alerts_generated: int):
        """Update flight log with mission results"""
        session = self.db_manager.db_manager.get_session()
        try:
            flight_log = session.query(DroneFlightLog).get(flight_log_id)
            if flight_log:
                drone_status = self.drone_system.get_drone_status()
                flight_log.end_time = datetime.now()
                flight_log.flight_status = "completed"
                flight_log.battery_end = drone_status["battery_level"]
                flight_log.images_captured = images_captured
                flight_log.risk_alerts_generated = alerts_generated
                
                if flight_log.start_time:
                    duration = datetime.now() - flight_log.start_time
                    flight_log.total_flight_time = int(duration.total_seconds() / 60)
                
                session.commit()
                
        finally:
            self.db_manager.db_manager.close_session(session)
    
    def check_sensor_status_and_activate_backup(self, mine_site_id: int = 1) -> Dict[str, Any]:
        """Check sensor status and activate drone backup if needed"""
        try:
            # Get sensor status from database
            failed_sensors = self._count_failed_sensors(mine_site_id)
            
            if failed_sensors >= self.sensor_failure_threshold and not self.drone_backup_active:
                # Activate drone backup mode
                return self._activate_sensor_backup_mode(mine_site_id)
            elif failed_sensors < self.sensor_failure_threshold and self.drone_backup_active:
                # Deactivate backup mode
                return self._deactivate_sensor_backup_mode()
            
            return {
                "success": True,
                "backup_mode": self.drone_backup_active,
                "failed_sensors": failed_sensors,
                "threshold": self.sensor_failure_threshold
            }
            
        except Exception as e:
            logger.error(f"Failed to check sensor status: {e}")
            return {"success": False, "message": str(e)}
    
    def _count_failed_sensors(self, mine_site_id: int) -> int:
        """Count the number of failed sensors"""
        # This would integrate with the existing sensor monitoring system
        # For now, simulate based on recent sensor readings
        session = self.db_manager.db_manager.get_session()
        try:
            from database.schema import Sensor, SensorReading
            
            # Check sensors that haven't reported in the last hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            # Get all active sensors
            active_sensors = session.query(Sensor).filter_by(
                mine_site_id=mine_site_id, status='active'
            ).all()
            
            failed_count = 0
            for sensor in active_sensors:
                recent_reading = session.query(SensorReading).filter_by(
                    sensor_id=sensor.id
                ).filter(SensorReading.timestamp >= cutoff_time).first()
                
                if not recent_reading:
                    failed_count += 1
            
            return failed_count
            
        finally:
            self.db_manager.db_manager.close_session(session)
    
    def _activate_sensor_backup_mode(self, mine_site_id: int) -> Dict[str, Any]:
        """Activate drone backup mode when sensors fail"""
        try:
            self.drone_backup_active = True
            
            # Start emergency drone mission
            emergency_result = self.drone_system.simulate_sensor_failure_detection()
            
            if emergency_result["success"]:
                # Log emergency mission
                flight_log = self._create_flight_log(mine_site_id, "emergency")
                
                # Process emergency results
                alerts_generated = 0
                for result in emergency_result.get("emergency_results", []):
                    analysis_id = self._store_image_analysis(
                        flight_log.id, mine_site_id, result
                    )
                    
                    # Generate alerts for high-risk areas
                    if result["analysis"]["risk_level"] in ["high", "critical"]:
                        if self._generate_drone_alert(analysis_id, mine_site_id, result):
                            alerts_generated += 1
                
                # Update flight log
                self._update_flight_log(
                    flight_log.id, 
                    len(emergency_result.get("emergency_results", [])), 
                    alerts_generated
                )
                
                # Send backup mode notification
                self._send_backup_mode_notification(mine_site_id, True)
                
                return {
                    "success": True,
                    "message": "Drone backup mode activated",
                    "emergency_scan_completed": True,
                    "high_risk_detected": emergency_result.get("high_risk_detected", False)
                }
            
            return emergency_result
            
        except Exception as e:
            logger.error(f"Failed to activate sensor backup mode: {e}")
            return {"success": False, "message": str(e)}
    
    def _deactivate_sensor_backup_mode(self) -> Dict[str, Any]:
        """Deactivate drone backup mode when sensors are restored"""
        self.drone_backup_active = False
        
        # Send notification about restored sensor operation
        self._send_backup_mode_notification(1, False)
        
        return {
            "success": True,
            "message": "Drone backup mode deactivated - sensors restored",
            "backup_mode": False
        }
    
    def _send_backup_mode_notification(self, mine_site_id: int, activated: bool):
        """Send notification about backup mode status"""
        try:
            if activated:
                message = """
🚨 SENSOR FAILURE DETECTED - DRONE BACKUP ACTIVATED

Multiple sensors have failed to report. Drone emergency monitoring is now active.
Continuous aerial surveillance has been initiated to maintain safety coverage.

Actions taken:
- Emergency drone patrol deployed
- High-risk areas scanned
- Alert system remains operational

Please check sensor connectivity and perform maintenance as needed.
"""
            else:
                message = """
✅ SENSOR SYSTEM RESTORED - DRONE BACKUP DEACTIVATED

Sensor connectivity has been restored. Returning to normal monitoring mode.
Drone backup monitoring has been successfully deactivated.

Normal sensor-based monitoring is now active.
"""
            
            self.notification_system.send_alert_notification(
                alert_type="sensor_backup_mode",
                risk_level="medium" if activated else "low",
                message=message,
                location={"lat": 39.7392, "lon": -104.9903}
            )
            
        except Exception as e:
            logger.error(f"Failed to send backup mode notification: {e}")
    
    def get_drone_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive drone monitoring status"""
        try:
            drone_status = self.drone_system.get_drone_status()
            recent_analyses = self.drone_system.get_recent_analysis_results(5)
            
            # Get database statistics
            session = self.db_manager.db_manager.get_session()
            try:
                # Count today's flights
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                todays_flights = session.query(DroneFlightLog).filter(
                    DroneFlightLog.start_time >= today
                ).count()
                
                # Count today's images
                todays_images = session.query(DroneImageAnalysis).filter(
                    DroneImageAnalysis.timestamp >= today
                ).count()
                
                # Count active drone alerts
                active_drone_alerts = session.query(DroneAlert).filter_by(resolved=False).count()
                
            finally:
                self.db_manager.db_manager.close_session(session)
            
            return {
                "drone_status": drone_status,
                "backup_mode_active": self.drone_backup_active,
                "recent_analyses": recent_analyses,
                "daily_stats": {
                    "flights_today": todays_flights,
                    "images_captured_today": todays_images,
                    "active_alerts": active_drone_alerts
                },
                "last_sensor_check": self.last_sensor_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get drone monitoring status: {e}")
            return {"success": False, "message": str(e)}