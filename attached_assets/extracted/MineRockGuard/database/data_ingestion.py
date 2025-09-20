"""
Data ingestion system for real-time sensor data and IoT integration
Handles MQTT, HTTP APIs, LoRaWAN, and other communication protocols
"""

import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from database.schema import DatabaseManager, Sensor, SensorReading, EnvironmentalData, CommunicationLog
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SensorData:
    """Standardized sensor data format"""
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str
    quality_score: float = 1.0
    metadata: Optional[Dict] = None

@dataclass
class EnvironmentalDataPoint:
    """Environmental data point"""
    mine_site_id: int
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    precipitation: Optional[float] = None
    atmospheric_pressure: Optional[float] = None
    seismic_activity: Optional[float] = None
    source: str = "unknown"

class IoTDataIngestion:
    """Main data ingestion system for IoT sensors"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.mqtt_client = None
        self.is_running = False
        
        # MQTT Configuration
        self.mqtt_broker = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.mqtt_topics = [
            'sensors/+/displacement',
            'sensors/+/strain',
            'sensors/+/pressure',
            'sensors/+/vibration',
            'sensors/+/tilt',
            'environmental/+/weather',
            'lorawan/+/data'
        ]
    
    def setup_mqtt(self):
        """Setup MQTT client for sensor data"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            logger.info(f"MQTT client connected to {self.mqtt_broker}:{self.mqtt_port}")
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT: {e}")
            # Continue without MQTT for demo purposes
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("Successfully connected to MQTT broker")
            # Subscribe to sensor topics
            for topic in self.mqtt_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split('/')
            payload = json.loads(msg.payload.decode())
            
            if topic_parts[0] == 'sensors':
                self._process_sensor_data(topic_parts, payload)
            elif topic_parts[0] == 'environmental':
                self._process_environmental_data(topic_parts, payload)
            elif topic_parts[0] == 'lorawan':
                self._process_lorawan_data(topic_parts, payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        logger.warning(f"MQTT client disconnected with code {rc}")
    
    def _process_sensor_data(self, topic_parts: List[str], payload: Dict):
        """Process individual sensor readings"""
        try:
            sensor_id = topic_parts[1]
            sensor_type = topic_parts[2]
            
            # Create sensor data object
            sensor_data = SensorData(
                sensor_id=sensor_id,
                timestamp=datetime.fromtimestamp(payload.get('timestamp', datetime.now().timestamp()), tz=timezone.utc),
                value=float(payload['value']),
                unit=payload.get('unit', ''),
                quality_score=payload.get('quality', 1.0),
                metadata=payload.get('metadata', {})
            )
            
            # Store in database
            self._store_sensor_reading(sensor_data)
            
            # Log communication
            self._log_communication('MQTT', 'inbound', f"sensor/{sensor_id}", 
                                  'sensor_data', json.dumps(payload))
            
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
    
    def _process_environmental_data(self, topic_parts: List[str], payload: Dict):
        """Process environmental sensor data"""
        try:
            station_id = topic_parts[1]
            
            env_data = EnvironmentalDataPoint(
                mine_site_id=payload.get('mine_site_id', 1),
                timestamp=datetime.fromtimestamp(payload.get('timestamp', datetime.now().timestamp()), tz=timezone.utc),
                temperature=payload.get('temperature'),
                humidity=payload.get('humidity'),
                wind_speed=payload.get('wind_speed'),
                wind_direction=payload.get('wind_direction'),
                precipitation=payload.get('precipitation'),
                atmospheric_pressure=payload.get('pressure'),
                seismic_activity=payload.get('seismic'),
                source=f"station_{station_id}"
            )
            
            self._store_environmental_data(env_data)
            
        except Exception as e:
            logger.error(f"Error processing environmental data: {e}")
    
    def _process_lorawan_data(self, topic_parts: List[str], payload: Dict):
        """Process LoRaWAN sensor data"""
        try:
            device_id = topic_parts[1]
            
            # Decode LoRaWAN payload
            decoded_data = self._decode_lorawan_payload(payload)
            
            for sensor_reading in decoded_data:
                self._store_sensor_reading(sensor_reading)
            
            # Log LoRaWAN communication
            self._log_communication('LoRaWAN', 'inbound', device_id, 
                                  'sensor_data', json.dumps(payload))
            
        except Exception as e:
            logger.error(f"Error processing LoRaWAN data: {e}")
    
    def _decode_lorawan_payload(self, payload: Dict) -> List[SensorData]:
        """Decode LoRaWAN payload into sensor readings"""
        readings = []
        
        try:
            # Simulate decoding different sensor types from LoRaWAN payload
            data = payload.get('data', {})
            device_id = payload.get('device_id', 'unknown')
            timestamp = datetime.fromtimestamp(payload.get('timestamp', datetime.now().timestamp()), tz=timezone.utc)
            
            # Example: Multiple sensor readings in one LoRaWAN message
            if 'displacement' in data:
                readings.append(SensorData(
                    sensor_id=f"{device_id}_displacement",
                    timestamp=timestamp,
                    value=data['displacement'],
                    unit='mm',
                    quality_score=data.get('rssi', -100) / -50.0  # Convert RSSI to quality score
                ))
            
            if 'strain' in data:
                readings.append(SensorData(
                    sensor_id=f"{device_id}_strain",
                    timestamp=timestamp,
                    value=data['strain'],
                    unit='µε',
                    quality_score=data.get('rssi', -100) / -50.0
                ))
            
        except Exception as e:
            logger.error(f"Error decoding LoRaWAN payload: {e}")
        
        return readings
    
    def _store_sensor_reading(self, sensor_data: SensorData):
        """Store sensor reading in database"""
        session = self.db_manager.get_session()
        try:
            # Find or create sensor
            sensor = session.query(Sensor).filter_by(sensor_id=sensor_data.sensor_id).first()
            
            if not sensor:
                # Create new sensor if not exists
                sensor = Sensor(
                    sensor_id=sensor_data.sensor_id,
                    mine_site_id=1,  # Default to first mine site
                    sensor_type=self._infer_sensor_type(sensor_data.sensor_id),
                    coordinates={'x': 0, 'y': 0, 'z': 0},  # Default coordinates
                    status='active',
                    communication_protocol='MQTT'
                )
                session.add(sensor)
                session.flush()
            
            # Create sensor reading
            reading = SensorReading(
                sensor_id=sensor.id,
                timestamp=sensor_data.timestamp,
                value=sensor_data.value,
                unit=sensor_data.unit,
                quality_score=sensor_data.quality_score,
                sensor_metadata=sensor_data.metadata
            )
            
            session.add(reading)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing sensor reading: {e}")
        finally:
            self.db_manager.close_session(session)
    
    def _store_environmental_data(self, env_data: EnvironmentalDataPoint):
        """Store environmental data in database"""
        session = self.db_manager.get_session()
        try:
            env_record = EnvironmentalData(
                mine_site_id=env_data.mine_site_id,
                timestamp=env_data.timestamp,
                temperature=env_data.temperature,
                humidity=env_data.humidity,
                wind_speed=env_data.wind_speed,
                wind_direction=env_data.wind_direction,
                precipitation=env_data.precipitation,
                atmospheric_pressure=env_data.atmospheric_pressure,
                seismic_activity=env_data.seismic_activity,
                source=env_data.source
            )
            
            session.add(env_record)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing environmental data: {e}")
        finally:
            self.db_manager.close_session(session)
    
    def _log_communication(self, protocol: str, direction: str, source: str, 
                          message_type: str, payload: str, success: bool = True):
        """Log communication events"""
        session = self.db_manager.get_session()
        try:
            comm_log = CommunicationLog(
                protocol=protocol,
                direction=direction,
                source=source,
                destination='system',
                message_type=message_type,
                payload=payload,
                success=success,
                mine_site_id=1  # Default mine site
            )
            
            session.add(comm_log)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging communication: {e}")
        finally:
            self.db_manager.close_session(session)
    
    def _infer_sensor_type(self, sensor_id: str) -> str:
        """Infer sensor type from sensor ID"""
        sensor_id_lower = sensor_id.lower()
        
        if 'displacement' in sensor_id_lower:
            return 'displacement'
        elif 'strain' in sensor_id_lower:
            return 'strain'
        elif 'pressure' in sensor_id_lower:
            return 'pressure'
        elif 'vibration' in sensor_id_lower:
            return 'vibration'
        elif 'tilt' in sensor_id_lower:
            return 'tilt'
        else:
            return 'unknown'
    
    async def start_ingestion(self):
        """Start the data ingestion system"""
        self.is_running = True
        logger.info("Starting IoT data ingestion system...")
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start MQTT loop
        if self.mqtt_client:
            self.mqtt_client.loop_start()
        
        # Keep the system running
        while self.is_running:
            await asyncio.sleep(1)
    
    def stop_ingestion(self):
        """Stop the data ingestion system"""
        self.is_running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        logger.info("IoT data ingestion system stopped")

# HTTP API endpoint handlers for direct sensor data submission
class HTTPDataHandler:
    """Handle HTTP API submissions for sensor data"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.ingestion = IoTDataIngestion()
    
    def submit_sensor_data(self, data: Dict) -> Dict[str, Any]:
        """Accept sensor data via HTTP API"""
        try:
            sensor_data = SensorData(
                sensor_id=data['sensor_id'],
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                value=float(data['value']),
                unit=data.get('unit', ''),
                quality_score=data.get('quality_score', 1.0),
                metadata=data.get('metadata', {})
            )
            
            self.ingestion._store_sensor_reading(sensor_data)
            
            return {"status": "success", "message": "Data stored successfully"}
            
        except Exception as e:
            logger.error(f"Error in HTTP data submission: {e}")
            return {"status": "error", "message": str(e)}
    
    def submit_environmental_data(self, data: Dict) -> Dict[str, Any]:
        """Accept environmental data via HTTP API"""
        try:
            env_data = EnvironmentalDataPoint(
                mine_site_id=data.get('mine_site_id', 1),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                wind_speed=data.get('wind_speed'),
                wind_direction=data.get('wind_direction'),
                precipitation=data.get('precipitation'),
                atmospheric_pressure=data.get('atmospheric_pressure'),
                seismic_activity=data.get('seismic_activity'),
                source=data.get('source', 'http_api')
            )
            
            self.ingestion._store_environmental_data(env_data)
            
            return {"status": "success", "message": "Environmental data stored successfully"}
            
        except Exception as e:
            logger.error(f"Error in HTTP environmental data submission: {e}")
            return {"status": "error", "message": str(e)}

# Global instances
iot_ingestion = IoTDataIngestion()
http_handler = HTTPDataHandler()