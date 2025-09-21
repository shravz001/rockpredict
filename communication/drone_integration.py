"""
Drone Integration Module
Integrates drone system with existing alert and monitoring infrastructure
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging
import threading
import time

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
        self.parallel_monitoring_active = False
        self.last_parallel_analysis = None
        self.current_drone_risk_level = "low"
        self.current_sensor_risk_level = "low"
        self.current_flight_log_id = None  # Track current flight log for parallel monitoring
        self.monitoring_interval = 30  # Seconds between drone captures
        self.monitoring_thread = None  # Background monitoring thread
        self.stop_monitoring = False  # Flag to stop background monitoring
        
    def start_routine_patrol(self, mine_site_id: int = 1) -> Dict[str, Any]:
        """Start routine drone patrol mission"""
        try:
            # Log flight start in database
            flight_log = self._create_flight_log(mine_site_id, "patrol")
            
            # Start drone mission
            mission_result = self.drone_system.start_flight_mission("patrol")
            
            if mission_result["success"]:
                # Perform image captures along flight path
                self._execute_patrol_mission(int(flight_log.id), mine_site_id)
                
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
    
    def start_parallel_monitoring(self, mine_site_id: int = 1) -> Dict[str, Any]:
        """Start continuous parallel monitoring with both sensors and drone"""
        try:
            logger.info("Starting parallel monitoring system")
            
            # Activate drone for continuous monitoring
            self.drone_system.is_active = True
            self.parallel_monitoring_active = True
            
            # Create initial flight log for parallel monitoring
            flight_log = self._create_flight_log(mine_site_id, "parallel_monitoring")
            self.current_flight_log_id = flight_log.id
            
            # Start background monitoring thread
            self._start_background_monitoring_thread(mine_site_id)
            
            # Perform initial capture
            self._start_continuous_drone_monitoring(mine_site_id)
            
            return {
                "success": True,
                "message": "Parallel monitoring system activated",
                "drone_active": True,
                "sensor_monitoring": True,
                "mode": "parallel",
                "flight_log_id": flight_log.id
            }
            
        except Exception as e:
            logger.error(f"Failed to start parallel monitoring: {e}")
            return {"success": False, "message": str(e)}
    
    def stop_parallel_monitoring(self) -> Dict[str, Any]:
        """Stop continuous parallel monitoring"""
        try:
            logger.info("Stopping parallel monitoring system")
            
            # Stop background monitoring
            self.stop_monitoring = True
            self.parallel_monitoring_active = False
            
            # Wait for thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            # Deactivate drone
            self.drone_system.is_active = False
            
            return {
                "success": True,
                "message": "Parallel monitoring system stopped",
                "drone_active": False,
                "sensor_monitoring": False,
                "mode": "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop parallel monitoring: {e}")
            return {"success": False, "message": str(e)}
    
    def _start_background_monitoring_thread(self, mine_site_id: int):
        """Start background thread for continuous monitoring"""
        def monitoring_loop():
            logger.info(f"Background monitoring thread started (interval: {self.monitoring_interval}s)")
            
            while not self.stop_monitoring and self.parallel_monitoring_active:
                try:
                    # Perform drone monitoring capture
                    self._start_continuous_drone_monitoring(mine_site_id)
                    
                    # Wait for next interval
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    logger.error(f"Background monitoring error: {e}")
                    time.sleep(5)  # Short delay on error
            
            logger.info("Background monitoring thread stopped")
        
        # Reset stop flag and start thread
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def get_parallel_predictions(self, mine_site_id: int = 1) -> Dict[str, Any]:
        """Get real-time predictions from both sensor and drone systems"""
        try:
            # Get sensor predictions (simulated for now)
            sensor_prediction = self._get_sensor_prediction(mine_site_id)
            
            # Get latest drone analysis
            drone_prediction = self._get_latest_drone_prediction(mine_site_id)
            
            # Combine predictions with confidence weighting
            combined_prediction = self._combine_predictions(sensor_prediction, drone_prediction)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "sensor_prediction": sensor_prediction,
                "drone_prediction": drone_prediction,
                "combined_prediction": combined_prediction,
                "monitoring_status": {
                    "sensors_active": self._check_sensors_status(mine_site_id),
                    "drone_active": self.drone_system.is_active,
                    "parallel_mode": self.parallel_monitoring_active
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get parallel predictions: {e}")
            return {"success": False, "message": str(e)}
    
    def _start_continuous_drone_monitoring(self, mine_site_id: int):
        """Perform drone monitoring capture and analysis"""
        try:
            if not self.current_flight_log_id:
                logger.warning("No active flight log for drone monitoring")
                return
                
            # Perform image capture and analysis
            location = {"lat": -23.5505, "lng": -46.6333, "altitude": 100}  # Mine location
            capture_result = self.drone_system.capture_and_analyze_image(location)
            
            if capture_result["success"]:
                # Store analysis
                analysis_id = self._store_image_analysis(
                    self.current_flight_log_id, mine_site_id, capture_result["result"]
                )
                
                # Update current drone risk level
                self.current_drone_risk_level = capture_result["result"]["analysis"]["risk_level"]
                self.last_parallel_analysis = datetime.now()
                
                # Generate alert if high risk detected
                if capture_result["risk_detected"]:
                    self._generate_drone_alert(analysis_id, mine_site_id, capture_result["result"])
                    
                logger.info(f"Drone analysis completed - Risk Level: {self.current_drone_risk_level}")
                
        except Exception as e:
            logger.error(f"Continuous drone monitoring error: {e}")
    
    def _get_sensor_prediction(self, mine_site_id: int) -> Dict[str, Any]:
        """Get current sensor-based prediction"""
        try:
            from models.rockfall_predictor import RockfallPredictor
            
            # Initialize predictor
            predictor = RockfallPredictor()
            
            # Get latest sensor data (simulated for now)
            sensor_data = self._get_latest_sensor_data(mine_site_id)
            
            # Make prediction
            prediction = predictor.predict_risk(sensor_data)
            self.current_sensor_risk_level = prediction["risk_level"]
            
            return {
                "risk_level": prediction["risk_level"],
                "risk_score": prediction["risk_probability"],
                "confidence": prediction["confidence"],
                "data_source": "sensors",
                "sensor_count": len(sensor_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sensor prediction error: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": 0.0,
                "confidence": 0.0,
                "data_source": "sensors",
                "error": str(e)
            }
    
    def _get_latest_drone_prediction(self, mine_site_id: int) -> Dict[str, Any]:
        """Get latest drone analysis prediction"""
        try:
            # Check if we need a fresh capture (for continuous monitoring)
            needs_fresh_capture = (
                not self.last_parallel_analysis or 
                (datetime.now() - self.last_parallel_analysis).total_seconds() > self.monitoring_interval
            )
            
            if needs_fresh_capture and self.parallel_monitoring_active:
                # Trigger new analysis for continuous monitoring
                self._start_continuous_drone_monitoring(mine_site_id)
            
            return {
                "risk_level": self.current_drone_risk_level,
                "risk_score": self._risk_level_to_score(self.current_drone_risk_level),
                "confidence": 0.85,  # Drone analysis confidence
                "data_source": "drone_imaging",
                "last_analysis": self.last_parallel_analysis.isoformat() if self.last_parallel_analysis else None,
                "timestamp": datetime.now().isoformat(),
                "seconds_since_capture": (datetime.now() - self.last_parallel_analysis).total_seconds() if self.last_parallel_analysis else 0
            }
            
        except Exception as e:
            logger.error(f"Drone prediction error: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": 0.0,
                "confidence": 0.0,
                "data_source": "drone_imaging",
                "error": str(e)
            }
    
    def _combine_predictions(self, sensor_pred: Dict, drone_pred: Dict) -> Dict[str, Any]:
        """Combine sensor and drone predictions with intelligent weighting"""
        try:
            # Weight based on data availability and confidence
            sensor_weight = 0.6 if sensor_pred.get("confidence", 0) > 0.5 else 0.3
            drone_weight = 0.4 if drone_pred.get("confidence", 0) > 0.5 else 0.7
            
            # Normalize weights
            total_weight = sensor_weight + drone_weight
            sensor_weight /= total_weight
            drone_weight /= total_weight
            
            # Combine risk scores
            sensor_score = sensor_pred.get("risk_score", 0)
            drone_score = drone_pred.get("risk_score", 0)
            combined_score = (sensor_score * sensor_weight) + (drone_score * drone_weight)
            
            # Determine combined risk level
            if combined_score >= 0.7:
                combined_risk = "critical"
            elif combined_score >= 0.5:
                combined_risk = "high"
            elif combined_score >= 0.3:
                combined_risk = "medium"
            else:
                combined_risk = "low"
            
            return {
                "risk_level": combined_risk,
                "risk_score": combined_score,
                "confidence": min(sensor_pred.get("confidence", 0), drone_pred.get("confidence", 0)),
                "sensor_weight": sensor_weight,
                "drone_weight": drone_weight,
                "agreement": self._calculate_prediction_agreement(sensor_pred, drone_pred),
                "data_sources": "sensors_and_drone"
            }
            
        except Exception as e:
            logger.error(f"Prediction combination error: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _risk_level_to_score(self, risk_level: str) -> float:
        """Convert risk level to numerical score"""
        risk_mapping = {
            "low": 0.2,
            "medium": 0.4,
            "high": 0.7,
            "critical": 0.9,
            "unknown": 0.0
        }
        return risk_mapping.get(risk_level, 0.0)
    
    def _calculate_prediction_agreement(self, sensor_pred: Dict, drone_pred: Dict) -> float:
        """Calculate agreement between sensor and drone predictions"""
        try:
            sensor_score = sensor_pred.get("risk_score", 0)
            drone_score = drone_pred.get("risk_score", 0)
            
            # Calculate similarity (1.0 = perfect agreement, 0.0 = complete disagreement)
            difference = abs(sensor_score - drone_score)
            agreement = max(0.0, 1.0 - difference)
            
            return round(agreement, 2)
            
        except Exception:
            return 0.0
    
    def _get_latest_sensor_data(self, mine_site_id: int) -> Dict[str, float]:
        """Get latest sensor readings (simulated for now)"""
        import random
        
        return {
            'displacement_rate': random.uniform(0.1, 2.0),
            'strain_magnitude': random.uniform(0.05, 1.5),
            'pore_pressure': random.uniform(10, 100),
            'temperature': random.uniform(15, 35),
            'rainfall': random.uniform(0, 50),
            'wind_speed': random.uniform(0, 25),
            'vibration_level': random.uniform(0.1, 5.0),
            'slope_angle': random.uniform(30, 70),
            'soil_moisture': random.uniform(10, 80),
            'crack_density': random.uniform(0.1, 2.0)
        }
    
    def _check_sensors_status(self, mine_site_id: int) -> bool:
        """Check if sensors are currently active and reporting"""
        try:
            # When parallel monitoring is active, sensors are considered active by default
            # since we're generating synthetic sensor data for the predictions
            if self.parallel_monitoring_active:
                return True
                
            session = self.db_manager.db_manager.get_session()
            from database.schema import Sensor, SensorReading
            
            # Check for recent sensor readings
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_readings = session.query(SensorReading).filter(
                SensorReading.timestamp >= cutoff_time
            ).count()
            
            return recent_readings > 0
            
        except Exception:
            return True  # Assume active if check fails
        finally:
            if 'session' in locals():
                self.db_manager.db_manager.close_session(session)
    
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
                        int(flight_log_id), mine_site_id, capture_result["result"]
                    )
                    
                    # Check if alert should be generated
                    if capture_result["risk_detected"]:
                        alert_generated = self._generate_drone_alert(
                            analysis_id, mine_site_id, capture_result["result"]
                        )
                        if alert_generated:
                            alerts_generated += 1
        
        # Update flight log with results
        self._update_flight_log(int(flight_log_id), images_captured, alerts_generated)
    
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