"""
Physical Siren System Integration and Emergency Response Protocols
Handles hardware siren control, emergency broadcast systems, and response coordination
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import requests
from database.database_manager import RockfallDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SirenType(Enum):
    """Types of emergency sirens"""
    WARNING = "warning"
    EVACUATION = "evacuation"
    ALL_CLEAR = "all_clear"
    TEST = "test"

class BroadcastChannel(Enum):
    """Emergency broadcast channels"""
    LOUDSPEAKER = "loudspeaker"
    RADIO_UHF = "radio_uhf"
    RADIO_VHF = "radio_vhf"
    PA_SYSTEM = "pa_system"
    MOBILE_ALERT = "mobile_alert"
    SATELLITE = "satellite"

@dataclass
class SirenDevice:
    """Physical siren device configuration"""
    siren_id: str
    device_type: str
    location: Dict[str, float]
    coverage_radius: float  # meters
    max_decibel: int
    power_source: str  # mains, battery, solar
    communication_method: str  # ethernet, radio, cellular
    
    # Status
    operational: bool = True
    last_test: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None

@dataclass
class EmergencyProtocol:
    """Emergency response protocol definition"""
    protocol_id: str
    name: str
    trigger_conditions: List[str]
    priority_level: int  # 1-5, 5 being highest
    
    # Response actions
    siren_pattern: str
    broadcast_channels: List[BroadcastChannel]
    voice_message: str
    auto_escalation: bool
    evacuation_required: bool
    
    # Timing
    activation_delay: int  # seconds
    duration: int  # seconds
    repeat_interval: int  # seconds

class SirenController:
    """Hardware siren control system"""
    
    def __init__(self):
        self.db_manager = RockfallDatabaseManager()
        self.sirens: Dict[str, SirenDevice] = {}
        self.active_alerts: Dict[str, Dict] = {}
        self.emergency_protocols: Dict[str, EmergencyProtocol] = {}
        self.is_running = False
        
        # Load configurations
        self._initialize_siren_devices()
        self._initialize_emergency_protocols()
        
        # Hardware interface simulation
        self.hardware_interface = self._initialize_hardware_interface()
    
    def _initialize_siren_devices(self):
        """Initialize siren device configurations"""
        # In production, this would load from database or configuration files
        default_sirens = [
            SirenDevice(
                siren_id="SIREN_NORTH_001",
                device_type="Whelen WPS-2900",
                location={"lat": 39.7402, "lon": -104.9913, "elevation": 1650},
                coverage_radius=1000,
                max_decibel=130,
                power_source="mains_battery_backup",
                communication_method="ethernet",
                operational=True,
                battery_level=95.0,
                signal_strength=-45.0
            ),
            SirenDevice(
                siren_id="SIREN_SOUTH_002",
                device_type="Federal Signal Modulator",
                location={"lat": 39.7382, "lon": -104.9893, "elevation": 1645},
                coverage_radius=800,
                max_decibel=125,
                power_source="solar_battery",
                communication_method="radio_uhf",
                operational=True,
                battery_level=87.0,
                signal_strength=-52.0
            ),
            SirenDevice(
                siren_id="SIREN_EAST_003",
                device_type="Acoustic Technology ATU",
                location={"lat": 39.7392, "lon": -104.9883, "elevation": 1655},
                coverage_radius=1200,
                max_decibel=135,
                power_source="mains",
                communication_method="cellular",
                operational=True,
                signal_strength=-38.0
            ),
            SirenDevice(
                siren_id="MOBILE_UNIT_004",
                device_type="Portable Emergency Siren",
                location={"lat": 39.7400, "lon": -104.9900, "elevation": 1650},
                coverage_radius=500,
                max_decibel=120,
                power_source="battery",
                communication_method="radio_vhf",
                operational=True,
                battery_level=78.0,
                signal_strength=-48.0
            )
        ]
        
        for siren in default_sirens:
            self.sirens[siren.siren_id] = siren
        
        logger.info(f"Initialized {len(self.sirens)} siren devices")
    
    def _initialize_emergency_protocols(self):
        """Initialize emergency response protocols"""
        protocols = [
            EmergencyProtocol(
                protocol_id="ROCKFALL_WARNING",
                name="Rockfall Warning",
                trigger_conditions=["high_risk_detected", "crack_propagation", "slope_instability"],
                priority_level=4,
                siren_pattern="alternating_tone",
                broadcast_channels=[BroadcastChannel.LOUDSPEAKER, BroadcastChannel.RADIO_UHF, BroadcastChannel.MOBILE_ALERT],
                voice_message="ATTENTION: Rockfall warning in effect. All personnel in affected areas move to safe zones immediately.",
                auto_escalation=True,
                evacuation_required=False,
                activation_delay=5,
                duration=60,
                repeat_interval=300
            ),
            EmergencyProtocol(
                protocol_id="IMMEDIATE_EVACUATION",
                name="Immediate Evacuation",
                trigger_conditions=["imminent_rockfall", "critical_instability", "major_crack_detected"],
                priority_level=5,
                siren_pattern="continuous_wail",
                broadcast_channels=[BroadcastChannel.LOUDSPEAKER, BroadcastChannel.RADIO_UHF, BroadcastChannel.RADIO_VHF, BroadcastChannel.PA_SYSTEM, BroadcastChannel.MOBILE_ALERT],
                voice_message="EMERGENCY EVACUATION: Immediate rockfall danger. All personnel evacuate affected areas NOW. Proceed to emergency assembly points.",
                auto_escalation=True,
                evacuation_required=True,
                activation_delay=0,
                duration=120,
                repeat_interval=180
            ),
            EmergencyProtocol(
                protocol_id="EQUIPMENT_FAILURE",
                name="Equipment Failure Alert",
                trigger_conditions=["sensor_network_failure", "communication_loss", "power_failure"],
                priority_level=2,
                siren_pattern="two_tone",
                broadcast_channels=[BroadcastChannel.RADIO_UHF, BroadcastChannel.MOBILE_ALERT],
                voice_message="Notice: Equipment failure detected. Maintenance teams respond to affected areas.",
                auto_escalation=False,
                evacuation_required=False,
                activation_delay=30,
                duration=30,
                repeat_interval=600
            ),
            EmergencyProtocol(
                protocol_id="ALL_CLEAR",
                name="All Clear Signal",
                trigger_conditions=["danger_passed", "manual_all_clear"],
                priority_level=1,
                siren_pattern="steady_tone",
                broadcast_channels=[BroadcastChannel.LOUDSPEAKER, BroadcastChannel.RADIO_UHF, BroadcastChannel.MOBILE_ALERT],
                voice_message="All clear. Normal operations may resume. Continue to exercise caution in previously affected areas.",
                auto_escalation=False,
                evacuation_required=False,
                activation_delay=0,
                duration=30,
                repeat_interval=0
            )
        ]
        
        for protocol in protocols:
            self.emergency_protocols[protocol.protocol_id] = protocol
        
        logger.info(f"Initialized {len(self.emergency_protocols)} emergency protocols")
    
    def _initialize_hardware_interface(self) -> Dict[str, Any]:
        """Initialize hardware interface (simulated)"""
        # In production, this would initialize actual hardware interfaces
        return {
            'ethernet_interface': {'status': 'connected', 'ip': '192.168.1.100'},
            'radio_uhf_interface': {'status': 'operational', 'frequency': '450.125'},
            'radio_vhf_interface': {'status': 'operational', 'frequency': '154.340'},
            'cellular_interface': {'status': 'connected', 'signal': -65},
            'pa_system_interface': {'status': 'operational', 'zones': 12}
        }
    
    def activate_emergency_protocol(self, protocol_id: str, trigger_reason: str, 
                                  affected_areas: List[Dict], manual_override: bool = False) -> bool:
        """Activate an emergency protocol"""
        try:
            if protocol_id not in self.emergency_protocols:
                logger.error(f"Unknown emergency protocol: {protocol_id}")
                return False
            
            protocol = self.emergency_protocols[protocol_id]
            
            # Check if already active
            if protocol_id in self.active_alerts:
                logger.warning(f"Protocol {protocol_id} already active")
                return True
            
            logger.info(f"Activating emergency protocol: {protocol.name}")
            
            # Create alert record
            alert_record = {
                'protocol_id': protocol_id,
                'trigger_reason': trigger_reason,
                'affected_areas': affected_areas,
                'activation_time': datetime.now(),
                'manual_override': manual_override,
                'status': 'activating'
            }
            
            self.active_alerts[protocol_id] = alert_record
            
            # Apply activation delay if not manual override
            if not manual_override and protocol.activation_delay > 0:
                logger.info(f"Applying {protocol.activation_delay}s activation delay")
                time.sleep(protocol.activation_delay)
            
            # Activate sirens with appropriate pattern
            affected_sirens = self._get_sirens_for_areas(affected_areas)
            for siren_id in affected_sirens:
                self._activate_siren(siren_id, protocol.siren_pattern, protocol.duration)
            
            # Broadcast voice message
            self._broadcast_voice_message(protocol.voice_message, protocol.broadcast_channels)
            
            # Send mobile alerts
            if BroadcastChannel.MOBILE_ALERT in protocol.broadcast_channels:
                self._send_mobile_alerts(protocol.voice_message, affected_areas)
            
            # Store in database
            self._log_emergency_activation(protocol_id, trigger_reason, affected_areas)
            
            # Update status
            alert_record['status'] = 'active'
            alert_record['sirens_activated'] = affected_sirens
            
            # Schedule repeat if configured
            if protocol.repeat_interval > 0:
                threading.Timer(
                    protocol.repeat_interval,
                    self._repeat_protocol,
                    args=[protocol_id]
                ).start()
            
            logger.info(f"Emergency protocol {protocol.name} activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating emergency protocol {protocol_id}: {e}")
            return False
    
    def _get_sirens_for_areas(self, affected_areas: List[Dict]) -> List[str]:
        """Get sirens that cover the affected areas"""
        affected_sirens = []
        
        for area in affected_areas:
            area_lat = area.get('lat', 0)
            area_lon = area.get('lon', 0)
            
            for siren_id, siren in self.sirens.items():
                if not siren.operational:
                    continue
                
                # Calculate distance (simplified)
                siren_lat = siren.location['lat']
                siren_lon = siren.location['lon']
                
                # Simplified distance calculation
                distance = ((area_lat - siren_lat) ** 2 + (area_lon - siren_lon) ** 2) ** 0.5 * 111000  # Rough conversion to meters
                
                if distance <= siren.coverage_radius:
                    if siren_id not in affected_sirens:
                        affected_sirens.append(siren_id)
        
        # If no specific sirens cover the area, activate all operational sirens
        if not affected_sirens:
            affected_sirens = [sid for sid, siren in self.sirens.items() if siren.operational]
        
        return affected_sirens
    
    def _activate_siren(self, siren_id: str, pattern: str, duration: int):
        """Activate a specific siren with given pattern"""
        try:
            if siren_id not in self.sirens:
                logger.error(f"Unknown siren: {siren_id}")
                return
            
            siren = self.sirens[siren_id]
            
            if not siren.operational:
                logger.warning(f"Siren {siren_id} not operational")
                return
            
            # In production, this would send actual hardware commands
            logger.info(f"Activating siren {siren_id} with pattern {pattern} for {duration}s")
            
            # Simulate hardware activation based on communication method
            if siren.communication_method == "ethernet":
                self._send_ethernet_command(siren_id, pattern, duration)
            elif siren.communication_method == "radio_uhf":
                self._send_radio_command(siren_id, pattern, duration, "UHF")
            elif siren.communication_method == "radio_vhf":
                self._send_radio_command(siren_id, pattern, duration, "VHF")
            elif siren.communication_method == "cellular":
                self._send_cellular_command(siren_id, pattern, duration)
            
            logger.info(f"Siren {siren_id} activation command sent")
            
        except Exception as e:
            logger.error(f"Error activating siren {siren_id}: {e}")
    
    def _send_ethernet_command(self, siren_id: str, pattern: str, duration: int):
        """Send siren command via Ethernet (simulated)"""
        # In production, this would use actual network protocols
        command = {
            'device_id': siren_id,
            'action': 'activate',
            'pattern': pattern,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Ethernet command to {siren_id}: {command}")
        # Simulate network call
        # requests.post(f"http://{siren.ip_address}/activate", json=command)
    
    def _send_radio_command(self, siren_id: str, pattern: str, duration: int, band: str):
        """Send siren command via radio (simulated)"""
        # In production, this would use radio communication protocols
        command = f"SIREN,{siren_id},{pattern},{duration}"
        
        logger.info(f"{band} radio command to {siren_id}: {command}")
        # Simulate radio transmission
    
    def _send_cellular_command(self, siren_id: str, pattern: str, duration: int):
        """Send siren command via cellular (simulated)"""
        # In production, this would use cellular/SMS/data protocols
        command = {
            'device_id': siren_id,
            'action': 'activate',
            'pattern': pattern,
            'duration': duration
        }
        
        logger.info(f"Cellular command to {siren_id}: {command}")
        # Simulate cellular command
    
    def _broadcast_voice_message(self, message: str, channels: List[BroadcastChannel]):
        """Broadcast voice message on specified channels"""
        logger.info(f"Broadcasting message on {len(channels)} channels: {message}")
        
        for channel in channels:
            try:
                if channel == BroadcastChannel.LOUDSPEAKER:
                    self._broadcast_loudspeaker(message)
                elif channel == BroadcastChannel.RADIO_UHF:
                    self._broadcast_radio(message, "UHF")
                elif channel == BroadcastChannel.RADIO_VHF:
                    self._broadcast_radio(message, "VHF")
                elif channel == BroadcastChannel.PA_SYSTEM:
                    self._broadcast_pa_system(message)
                elif channel == BroadcastChannel.SATELLITE:
                    self._broadcast_satellite(message)
                    
            except Exception as e:
                logger.error(f"Error broadcasting on {channel.value}: {e}")
    
    def _broadcast_loudspeaker(self, message: str):
        """Broadcast via loudspeaker system"""
        logger.info(f"Loudspeaker broadcast: {message}")
        # In production, this would interface with PA system
    
    def _broadcast_radio(self, message: str, band: str):
        """Broadcast via radio system"""
        logger.info(f"{band} radio broadcast: {message}")
        # In production, this would interface with radio system
    
    def _broadcast_pa_system(self, message: str):
        """Broadcast via PA system"""
        logger.info(f"PA system broadcast: {message}")
        # In production, this would interface with building PA system
    
    def _broadcast_satellite(self, message: str):
        """Broadcast via satellite communication"""
        logger.info(f"Satellite broadcast: {message}")
        # In production, this would use satellite communication
    
    def _send_mobile_alerts(self, message: str, affected_areas: List[Dict]):
        """Send mobile alerts to personnel in affected areas"""
        logger.info(f"Sending mobile alerts for {len(affected_areas)} areas")
        
        # In production, this would integrate with mobile alert systems
        # For now, simulate sending alerts
        
        for area in affected_areas:
            logger.info(f"Mobile alert for area {area}: {message}")
    
    def _log_emergency_activation(self, protocol_id: str, trigger_reason: str, affected_areas: List[Dict]):
        """Log emergency activation in database"""
        try:
            # Create alert in main database
            alert_id = self.db_manager.create_alert(
                mine_site_id=1,
                alert_type="emergency_protocol",
                severity="high",
                title=f"Emergency Protocol Activated: {protocol_id}",
                message=f"Trigger: {trigger_reason}",
                location=affected_areas[0] if affected_areas else None,
                triggered_by="siren_control_system"
            )
            
            logger.info(f"Emergency activation logged with alert ID: {alert_id}")
            
        except Exception as e:
            logger.error(f"Error logging emergency activation: {e}")
    
    def _repeat_protocol(self, protocol_id: str):
        """Repeat an active protocol"""
        if protocol_id not in self.active_alerts:
            return
        
        alert_record = self.active_alerts[protocol_id]
        protocol = self.emergency_protocols[protocol_id]
        
        logger.info(f"Repeating emergency protocol: {protocol.name}")
        
        # Reactivate sirens
        for siren_id in alert_record.get('sirens_activated', []):
            self._activate_siren(siren_id, protocol.siren_pattern, protocol.duration)
        
        # Rebroadcast message
        self._broadcast_voice_message(protocol.voice_message, protocol.broadcast_channels)
        
        # Schedule next repeat if still active
        if protocol.repeat_interval > 0 and protocol_id in self.active_alerts:
            threading.Timer(
                protocol.repeat_interval,
                self._repeat_protocol,
                args=[protocol_id]
            ).start()
    
    def deactivate_protocol(self, protocol_id: str, reason: str = "manual_deactivation") -> bool:
        """Deactivate an emergency protocol"""
        try:
            if protocol_id not in self.active_alerts:
                logger.warning(f"Protocol {protocol_id} not active")
                return True
            
            alert_record = self.active_alerts[protocol_id]
            
            logger.info(f"Deactivating emergency protocol: {protocol_id}")
            
            # Stop all sirens for this protocol
            for siren_id in alert_record.get('sirens_activated', []):
                self._deactivate_siren(siren_id)
            
            # Remove from active alerts
            del self.active_alerts[protocol_id]
            
            # Log deactivation
            logger.info(f"Emergency protocol {protocol_id} deactivated - Reason: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating protocol {protocol_id}: {e}")
            return False
    
    def _deactivate_siren(self, siren_id: str):
        """Deactivate a specific siren"""
        try:
            logger.info(f"Deactivating siren {siren_id}")
            
            siren = self.sirens[siren_id]
            
            # Send deactivation command based on communication method
            if siren.communication_method == "ethernet":
                self._send_ethernet_command(siren_id, "stop", 0)
            elif siren.communication_method == "radio_uhf":
                self._send_radio_command(siren_id, "stop", 0, "UHF")
            elif siren.communication_method == "radio_vhf":
                self._send_radio_command(siren_id, "stop", 0, "VHF")
            elif siren.communication_method == "cellular":
                self._send_cellular_command(siren_id, "stop", 0)
            
            logger.info(f"Siren {siren_id} deactivation command sent")
            
        except Exception as e:
            logger.error(f"Error deactivating siren {siren_id}: {e}")
    
    def test_siren_system(self, siren_id: Optional[str] = None) -> Dict[str, Any]:
        """Test siren system functionality"""
        test_results = {}
        
        try:
            sirens_to_test = [siren_id] if siren_id else list(self.sirens.keys())
            
            for sid in sirens_to_test:
                if sid not in self.sirens:
                    test_results[sid] = {"status": "error", "message": "Siren not found"}
                    continue
                
                siren = self.sirens[sid]
                
                logger.info(f"Testing siren {sid}")
                
                # Test communication
                comm_test = self._test_siren_communication(sid)
                
                # Test audio output (simulated)
                audio_test = self._test_siren_audio(sid)
                
                # Update last test time
                siren.last_test = datetime.now()
                
                test_results[sid] = {
                    "status": "pass" if comm_test and audio_test else "fail",
                    "communication": comm_test,
                    "audio_output": audio_test,
                    "battery_level": siren.battery_level,
                    "signal_strength": siren.signal_strength,
                    "last_test": siren.last_test.isoformat()
                }
            
            logger.info(f"Siren system test completed for {len(sirens_to_test)} devices")
            
        except Exception as e:
            logger.error(f"Error during siren system test: {e}")
            test_results["error"] = str(e)
        
        return test_results
    
    def _test_siren_communication(self, siren_id: str) -> bool:
        """Test communication with a siren"""
        try:
            # In production, this would send actual test commands
            logger.info(f"Testing communication with siren {siren_id}")
            
            # Simulate communication test
            siren = self.sirens[siren_id]
            
            # Check signal strength
            if siren.signal_strength and siren.signal_strength < -80:
                logger.warning(f"Weak signal for siren {siren_id}: {siren.signal_strength} dBm")
                return False
            
            # Simulate successful communication
            return True
            
        except Exception as e:
            logger.error(f"Communication test failed for siren {siren_id}: {e}")
            return False
    
    def _test_siren_audio(self, siren_id: str) -> bool:
        """Test audio output of a siren"""
        try:
            logger.info(f"Testing audio output for siren {siren_id}")
            
            # In production, this would activate the siren briefly for testing
            self._activate_siren(siren_id, "test", 5)  # 5-second test
            
            # Simulate successful audio test
            return True
            
        except Exception as e:
            logger.error(f"Audio test failed for siren {siren_id}: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall siren system status"""
        try:
            total_sirens = len(self.sirens)
            operational_sirens = sum(1 for s in self.sirens.values() if s.operational)
            
            # Battery status
            battery_sirens = [s for s in self.sirens.values() if s.battery_level is not None]
            avg_battery = sum(s.battery_level for s in battery_sirens) / len(battery_sirens) if battery_sirens else 0
            
            # Signal strength
            signal_sirens = [s for s in self.sirens.values() if s.signal_strength is not None]
            avg_signal = sum(s.signal_strength for s in signal_sirens) / len(signal_sirens) if signal_sirens else 0
            
            # Last test times
            tested_sirens = [s for s in self.sirens.values() if s.last_test is not None]
            oldest_test = min((s.last_test for s in tested_sirens), default=None)
            
            status = {
                "total_sirens": total_sirens,
                "operational_sirens": operational_sirens,
                "offline_sirens": total_sirens - operational_sirens,
                "average_battery_level": avg_battery,
                "average_signal_strength": avg_signal,
                "active_protocols": len(self.active_alerts),
                "oldest_test_date": oldest_test.isoformat() if oldest_test else None,
                "system_health": "good" if operational_sirens >= total_sirens * 0.8 else "degraded",
                "individual_sirens": [
                    {
                        "siren_id": sid,
                        "operational": siren.operational,
                        "battery_level": siren.battery_level,
                        "signal_strength": siren.signal_strength,
                        "last_test": siren.last_test.isoformat() if siren.last_test else None
                    }
                    for sid, siren in self.sirens.items()
                ]
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}

# Global siren controller instance
siren_controller = SirenController()