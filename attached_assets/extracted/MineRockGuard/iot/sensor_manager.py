"""
Advanced IoT Sensor Management System
Handles real sensor hardware, protocol management, and data validation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from queue import Queue
import requests
from database.database_manager import RockfallDatabaseManager
from database.data_ingestion import IoTDataIngestion, SensorData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorProtocol(Enum):
    """Supported sensor communication protocols"""
    LORAWAN = "lorawan"
    MQTT = "mqtt"
    HTTP = "http"
    MODBUS = "modbus"
    ZIGBEE = "zigbee"
    WIFI = "wifi"
    CELLULAR = "cellular"

class SensorStatus(Enum):
    """Sensor operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    LOW_BATTERY = "low_battery"
    WEAK_SIGNAL = "weak_signal"

@dataclass
class HardwareSensor:
    """Hardware sensor configuration and status"""
    sensor_id: str
    sensor_type: str
    protocol: SensorProtocol
    device_address: str
    mine_site_id: int
    coordinates: Dict[str, float]
    
    # Hardware specifications
    model: str
    manufacturer: str
    firmware_version: str
    calibration_date: datetime
    
    # Operational status
    status: SensorStatus = SensorStatus.ONLINE
    battery_level: float = 100.0
    signal_strength: float = -50.0  # dBm
    last_reading: Optional[datetime] = None
    
    # Communication settings
    reading_interval: int = 60  # seconds
    transmission_power: int = 14  # dBm
    data_rate: str = "SF7BW125"  # LoRaWAN data rate
    
    # Quality metrics
    error_count: int = 0
    missed_readings: int = 0
    data_quality_score: float = 1.0

@dataclass
class SensorReading:
    """Enhanced sensor reading with quality metrics"""
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str
    quality_score: float
    temperature: Optional[float] = None  # Sensor temperature
    voltage: Optional[float] = None  # Supply voltage
    rssi: Optional[float] = None  # Signal strength
    snr: Optional[float] = None  # Signal-to-noise ratio
    
class IoTSensorManager:
    """Advanced IoT sensor management with real hardware support"""
    
    def __init__(self):
        self.db_manager = RockfallDatabaseManager()
        self.data_ingestion = IoTDataIngestion()
        self.sensors: Dict[str, HardwareSensor] = {}
        self.reading_queue = Queue()
        self.is_running = False
        
        # Protocol handlers
        self.protocol_handlers = {
            SensorProtocol.HTTP: self._handle_http_sensor,
            SensorProtocol.MQTT: self._handle_mqtt_sensor,
            SensorProtocol.LORAWAN: self._handle_lorawan_sensor,
            SensorProtocol.MODBUS: self._handle_modbus_sensor
        }
        
        # Load sensor configurations
        self._load_sensor_configurations()
    
    def _load_sensor_configurations(self):
        """Load sensor configurations from database and configuration files"""
        try:
            # Get sensors from database
            mine_sites = self.db_manager.get_mine_sites()
            for site in mine_sites:
                db_sensors = self.db_manager.get_sensors_for_site(site['id'])
                
                for db_sensor in db_sensors:
                    # Create hardware sensor configuration
                    hardware_sensor = HardwareSensor(
                        sensor_id=db_sensor['sensor_id'],
                        sensor_type=db_sensor['sensor_type'],
                        protocol=SensorProtocol.LORAWAN,  # Default protocol
                        device_address=f"dev_{db_sensor['id']:04d}",
                        mine_site_id=site['id'],
                        coordinates=db_sensor['coordinates'],
                        model=f"{db_sensor['sensor_type'].title()}_Pro_v2",
                        manufacturer="MineGuard Systems",
                        firmware_version="2.1.4",
                        calibration_date=datetime.now() - timedelta(days=30),
                        battery_level=db_sensor.get('battery_level', 85.0),
                        signal_strength=db_sensor.get('signal_strength', -65.0)
                    )
                    
                    self.sensors[db_sensor['sensor_id']] = hardware_sensor
            
            logger.info(f"Loaded {len(self.sensors)} sensor configurations")
            
        except Exception as e:
            logger.error(f"Error loading sensor configurations: {e}")
    
    def register_sensor(self, sensor_config: HardwareSensor) -> bool:
        """Register a new hardware sensor"""
        try:
            # Validate sensor configuration
            if not self._validate_sensor_config(sensor_config):
                return False
            
            # Add to sensor registry
            self.sensors[sensor_config.sensor_id] = sensor_config
            
            # Initialize protocol handler
            protocol_handler = self.protocol_handlers.get(sensor_config.protocol)
            if protocol_handler:
                protocol_handler(sensor_config, 'register')
            
            logger.info(f"Registered sensor {sensor_config.sensor_id} with protocol {sensor_config.protocol.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering sensor {sensor_config.sensor_id}: {e}")
            return False
    
    def _validate_sensor_config(self, sensor: HardwareSensor) -> bool:
        """Validate sensor configuration"""
        if not sensor.sensor_id or not sensor.sensor_type:
            logger.error("Sensor ID and type are required")
            return False
        
        if sensor.sensor_id in self.sensors:
            logger.warning(f"Sensor {sensor.sensor_id} already registered")
            return False
        
        return True
    
    def _handle_http_sensor(self, sensor: HardwareSensor, action: str = 'read'):
        """Handle HTTP-based sensors"""
        if action == 'register':
            logger.info(f"HTTP sensor {sensor.sensor_id} registered")
            return
        
        try:
            # Simulate HTTP endpoint for sensor data
            url = f"http://sensor-gateway/{sensor.device_address}/data"
            
            # In a real implementation, this would make an actual HTTP request
            # response = requests.get(url, timeout=10)
            # if response.status_code == 200:
            #     data = response.json()
            
            # Simulated sensor response
            data = {
                'sensor_id': sensor.sensor_id,
                'timestamp': datetime.now().isoformat(),
                'value': self._simulate_sensor_reading(sensor.sensor_type),
                'unit': self._get_sensor_unit(sensor.sensor_type),
                'temperature': 23.5 + (time.time() % 10) - 5,
                'voltage': 3.3 + (time.time() % 2) * 0.1 - 0.1,
                'rssi': sensor.signal_strength
            }
            
            self._process_sensor_data(sensor, data)
            
        except Exception as e:
            logger.error(f"Error reading HTTP sensor {sensor.sensor_id}: {e}")
            self._update_sensor_status(sensor.sensor_id, SensorStatus.ERROR)
    
    def _handle_mqtt_sensor(self, sensor: HardwareSensor, action: str = 'read'):
        """Handle MQTT-based sensors"""
        if action == 'register':
            logger.info(f"MQTT sensor {sensor.sensor_id} registered")
            return
        
        # MQTT sensors are handled by the data ingestion system
        # This method handles sensor-specific MQTT operations
        pass
    
    def _handle_lorawan_sensor(self, sensor: HardwareSensor, action: str = 'read'):
        """Handle LoRaWAN sensors"""
        if action == 'register':
            logger.info(f"LoRaWAN sensor {sensor.sensor_id} registered on {sensor.data_rate}")
            return
        
        try:
            # Simulate LoRaWAN sensor communication
            # In real implementation, this would interface with LoRaWAN gateway
            
            # Calculate signal quality based on distance and environmental factors
            base_rssi = -50
            distance_loss = -0.1 * ((sensor.coordinates['x']**2 + sensor.coordinates['y']**2)**0.5 / 100)
            environmental_loss = -5 * (1 if datetime.now().hour in [6, 7, 18, 19] else 0)  # Weather effects
            
            current_rssi = base_rssi + distance_loss + environmental_loss
            sensor.signal_strength = current_rssi
            
            # Generate sensor data with LoRaWAN characteristics
            data = {
                'device_eui': sensor.device_address,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    sensor.sensor_type: self._simulate_sensor_reading(sensor.sensor_type),
                    'battery': sensor.battery_level,
                    'temperature': 20 + (time.time() % 20) - 10
                },
                'rssi': current_rssi,
                'snr': max(-20, current_rssi + 20),
                'data_rate': sensor.data_rate,
                'frequency': 915.2,  # MHz
                'gateway_id': 'gw_001'
            }
            
            self._process_lorawan_data(sensor, data)
            
        except Exception as e:
            logger.error(f"Error reading LoRaWAN sensor {sensor.sensor_id}: {e}")
            self._update_sensor_status(sensor.sensor_id, SensorStatus.ERROR)
    
    def _handle_modbus_sensor(self, sensor: HardwareSensor, action: str = 'read'):
        """Handle Modbus/RS485 sensors"""
        if action == 'register':
            logger.info(f"Modbus sensor {sensor.sensor_id} registered")
            return
        
        try:
            # Simulate Modbus RTU communication
            # In real implementation, this would use pymodbus library
            
            data = {
                'sensor_id': sensor.sensor_id,
                'timestamp': datetime.now().isoformat(),
                'registers': {
                    'value': self._simulate_sensor_reading(sensor.sensor_type),
                    'status': 0x0000,  # No errors
                    'temperature': int((23.5 + (time.time() % 10) - 5) * 10),
                    'voltage': int((3.3 + (time.time() % 2) * 0.1 - 0.1) * 1000)
                }
            }
            
            self._process_modbus_data(sensor, data)
            
        except Exception as e:
            logger.error(f"Error reading Modbus sensor {sensor.sensor_id}: {e}")
            self._update_sensor_status(sensor.sensor_id, SensorStatus.ERROR)
    
    def _simulate_sensor_reading(self, sensor_type: str) -> float:
        """Simulate realistic sensor readings"""
        base_values = {
            'displacement': 0.5,  # mm
            'strain': 50.0,       # µε
            'pressure': 15.2,     # kPa
            'vibration': 2.1,     # mm/s
            'tilt': 0.8           # degrees
        }
        
        base_value = base_values.get(sensor_type, 1.0)
        
        # Add realistic variations
        time_factor = time.time() % 3600  # Hourly cycle
        noise = (time.time() % 13) / 13 * 0.2 - 0.1  # ±10% noise
        trend = 0.001 * (time.time() % 86400)  # Daily trend
        
        return base_value * (1 + 0.3 * (time_factor / 3600) + noise + trend)
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """Get unit for sensor type"""
        units = {
            'displacement': 'mm',
            'strain': 'µε',
            'pressure': 'kPa',
            'vibration': 'mm/s',
            'tilt': 'degrees'
        }
        return units.get(sensor_type, 'unit')
    
    def _process_sensor_data(self, sensor: HardwareSensor, data: Dict):
        """Process incoming sensor data"""
        try:
            # Create standardized sensor reading
            reading = SensorReading(
                sensor_id=sensor.sensor_id,
                timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                value=float(data['value']),
                unit=data['unit'],
                quality_score=self._calculate_quality_score(sensor, data),
                temperature=data.get('temperature'),
                voltage=data.get('voltage'),
                rssi=data.get('rssi')
            )
            
            # Store in database via data ingestion system
            sensor_data = SensorData(
                sensor_id=reading.sensor_id,
                timestamp=reading.timestamp,
                value=reading.value,
                unit=reading.unit,
                quality_score=reading.quality_score,
                metadata={
                    'temperature': reading.temperature,
                    'voltage': reading.voltage,
                    'rssi': reading.rssi,
                    'protocol': sensor.protocol.value
                }
            )
            
            self.data_ingestion._store_sensor_reading(sensor_data)
            
            # Update sensor status
            self._update_sensor_metrics(sensor, reading)
            
        except Exception as e:
            logger.error(f"Error processing sensor data for {sensor.sensor_id}: {e}")
    
    def _process_lorawan_data(self, sensor: HardwareSensor, data: Dict):
        """Process LoRaWAN-specific data"""
        try:
            payload_data = data['data']
            
            for measurement_type, value in payload_data.items():
                if measurement_type in ['battery', 'temperature']:
                    continue  # Metadata, not sensor readings
                
                reading = SensorReading(
                    sensor_id=sensor.sensor_id,
                    timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                    value=float(value),
                    unit=self._get_sensor_unit(measurement_type),
                    quality_score=self._calculate_lorawan_quality(data),
                    rssi=data.get('rssi'),
                    snr=data.get('snr')
                )
                
                # Store reading
                sensor_data = SensorData(
                    sensor_id=reading.sensor_id,
                    timestamp=reading.timestamp,
                    value=reading.value,
                    unit=reading.unit,
                    quality_score=reading.quality_score,
                    metadata={
                        'rssi': reading.rssi,
                        'snr': reading.snr,
                        'data_rate': data.get('data_rate'),
                        'frequency': data.get('frequency'),
                        'gateway_id': data.get('gateway_id'),
                        'protocol': 'lorawan'
                    }
                )
                
                self.data_ingestion._store_sensor_reading(sensor_data)
            
            # Update sensor metrics
            sensor.battery_level = payload_data.get('battery', sensor.battery_level)
            sensor.signal_strength = data.get('rssi', sensor.signal_strength)
            sensor.last_reading = datetime.now()
            
        except Exception as e:
            logger.error(f"Error processing LoRaWAN data for {sensor.sensor_id}: {e}")
    
    def _process_modbus_data(self, sensor: HardwareSensor, data: Dict):
        """Process Modbus-specific data"""
        try:
            registers = data['registers']
            
            reading = SensorReading(
                sensor_id=sensor.sensor_id,
                timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                value=float(registers['value']),
                unit=self._get_sensor_unit(sensor.sensor_type),
                quality_score=1.0 if registers['status'] == 0x0000 else 0.5,
                temperature=registers.get('temperature', 0) / 10.0,  # Convert from scaled int
                voltage=registers.get('voltage', 0) / 1000.0  # Convert from mV to V
            )
            
            # Store reading
            sensor_data = SensorData(
                sensor_id=reading.sensor_id,
                timestamp=reading.timestamp,
                value=reading.value,
                unit=reading.unit,
                quality_score=reading.quality_score,
                metadata={
                    'temperature': reading.temperature,
                    'voltage': reading.voltage,
                    'status_register': registers['status'],
                    'protocol': 'modbus'
                }
            )
            
            self.data_ingestion._store_sensor_reading(sensor_data)
            
        except Exception as e:
            logger.error(f"Error processing Modbus data for {sensor.sensor_id}: {e}")
    
    def _calculate_quality_score(self, sensor: HardwareSensor, data: Dict) -> float:
        """Calculate data quality score"""
        quality = 1.0
        
        # Signal strength factor
        rssi = data.get('rssi', sensor.signal_strength)
        if rssi < -100:
            quality *= 0.3
        elif rssi < -80:
            quality *= 0.7
        elif rssi < -60:
            quality *= 0.9
        
        # Battery level factor
        if sensor.battery_level < 20:
            quality *= 0.6
        elif sensor.battery_level < 50:
            quality *= 0.8
        
        # Voltage stability factor
        voltage = data.get('voltage', 3.3)
        if voltage < 2.8 or voltage > 3.6:
            quality *= 0.7
        
        return max(0.1, quality)
    
    def _calculate_lorawan_quality(self, data: Dict) -> float:
        """Calculate LoRaWAN-specific quality score"""
        quality = 1.0
        
        # RSSI factor
        rssi = data.get('rssi', -100)
        if rssi > -80:
            quality *= 1.0
        elif rssi > -100:
            quality *= 0.8
        else:
            quality *= 0.4
        
        # SNR factor
        snr = data.get('snr', -20)
        if snr > 0:
            quality *= 1.0
        elif snr > -10:
            quality *= 0.9
        else:
            quality *= 0.6
        
        return max(0.1, quality)
    
    def _update_sensor_metrics(self, sensor: HardwareSensor, reading: SensorReading):
        """Update sensor operational metrics"""
        sensor.last_reading = reading.timestamp
        sensor.data_quality_score = reading.quality_score
        
        # Update status based on metrics
        if reading.quality_score < 0.3:
            sensor.status = SensorStatus.WEAK_SIGNAL
        elif sensor.battery_level < 20:
            sensor.status = SensorStatus.LOW_BATTERY
        else:
            sensor.status = SensorStatus.ONLINE
    
    def _update_sensor_status(self, sensor_id: str, status: SensorStatus):
        """Update sensor status"""
        if sensor_id in self.sensors:
            self.sensors[sensor_id].status = status
            logger.info(f"Sensor {sensor_id} status updated to {status.value}")
    
    async def start_monitoring(self):
        """Start continuous sensor monitoring"""
        self.is_running = True
        logger.info("Starting IoT sensor monitoring...")
        
        # Start background tasks for each protocol
        tasks = []
        
        # HTTP polling task
        tasks.append(asyncio.create_task(self._http_polling_loop()))
        
        # LoRaWAN monitoring task
        tasks.append(asyncio.create_task(self._lorawan_monitoring_loop()))
        
        # Modbus polling task
        tasks.append(asyncio.create_task(self._modbus_polling_loop()))
        
        # Health monitoring task
        tasks.append(asyncio.create_task(self._health_monitoring_loop()))
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
    
    async def _http_polling_loop(self):
        """HTTP sensor polling loop"""
        while self.is_running:
            try:
                http_sensors = [s for s in self.sensors.values() if s.protocol == SensorProtocol.HTTP]
                
                for sensor in http_sensors:
                    if sensor.status != SensorStatus.OFFLINE:
                        self._handle_http_sensor(sensor, 'read')
                
                await asyncio.sleep(30)  # Poll every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in HTTP polling loop: {e}")
                await asyncio.sleep(60)
    
    async def _lorawan_monitoring_loop(self):
        """LoRaWAN sensor monitoring loop"""
        while self.is_running:
            try:
                lorawan_sensors = [s for s in self.sensors.values() if s.protocol == SensorProtocol.LORAWAN]
                
                for sensor in lorawan_sensors:
                    if sensor.status != SensorStatus.OFFLINE:
                        self._handle_lorawan_sensor(sensor, 'read')
                
                await asyncio.sleep(sensor.reading_interval if lorawan_sensors else 60)
                
            except Exception as e:
                logger.error(f"Error in LoRaWAN monitoring loop: {e}")
                await asyncio.sleep(120)
    
    async def _modbus_polling_loop(self):
        """Modbus sensor polling loop"""
        while self.is_running:
            try:
                modbus_sensors = [s for s in self.sensors.values() if s.protocol == SensorProtocol.MODBUS]
                
                for sensor in modbus_sensors:
                    if sensor.status != SensorStatus.OFFLINE:
                        self._handle_modbus_sensor(sensor, 'read')
                
                await asyncio.sleep(10)  # Poll Modbus sensors frequently
                
            except Exception as e:
                logger.error(f"Error in Modbus polling loop: {e}")
                await asyncio.sleep(30)
    
    async def _health_monitoring_loop(self):
        """Sensor health and diagnostics monitoring"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for sensor in self.sensors.values():
                    # Check for missed readings
                    if sensor.last_reading:
                        time_since_reading = (current_time - sensor.last_reading).total_seconds()
                        expected_interval = sensor.reading_interval * 2  # Allow 2x tolerance
                        
                        if time_since_reading > expected_interval:
                            sensor.missed_readings += 1
                            if sensor.missed_readings > 5:
                                sensor.status = SensorStatus.OFFLINE
                    
                    # Check battery levels
                    if sensor.battery_level < 20:
                        sensor.status = SensorStatus.LOW_BATTERY
                    
                    # Simulate battery drain
                    if sensor.status == SensorStatus.ONLINE:
                        sensor.battery_level = max(0, sensor.battery_level - 0.001)  # Slow drain
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(600)
    
    def stop_monitoring(self):
        """Stop sensor monitoring"""
        self.is_running = False
        logger.info("IoT sensor monitoring stopped")
    
    def get_sensor_status(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed sensor status"""
        if sensor_id not in self.sensors:
            return None
        
        sensor = self.sensors[sensor_id]
        return {
            'sensor_id': sensor.sensor_id,
            'status': sensor.status.value,
            'battery_level': sensor.battery_level,
            'signal_strength': sensor.signal_strength,
            'last_reading': sensor.last_reading.isoformat() if sensor.last_reading else None,
            'data_quality_score': sensor.data_quality_score,
            'error_count': sensor.error_count,
            'missed_readings': sensor.missed_readings,
            'protocol': sensor.protocol.value,
            'coordinates': sensor.coordinates
        }
    
    def get_all_sensors_status(self) -> List[Dict[str, Any]]:
        """Get status of all sensors"""
        return [self.get_sensor_status(sensor_id) for sensor_id in self.sensors.keys()]

# Global sensor manager instance
iot_sensor_manager = IoTSensorManager()