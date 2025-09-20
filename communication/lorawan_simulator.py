import numpy as np
import random
from datetime import datetime, timedelta
import json

class LoRaWANSimulator:
    def __init__(self):
        self.gateways = self._initialize_gateways()
        self.devices = self._initialize_devices()
        self.radio_channels = self._initialize_radio_channels()
        self.network_status = {
            'uptime': 0.995,
            'total_messages': 0,
            'failed_messages': 0,
            'last_update': datetime.now()
        }
    
    def _initialize_gateways(self):
        """Initialize LoRaWAN gateways around the mine site"""
        gateways = []
        
        # Main gateways positioned strategically around the mine
        gateway_positions = [
            {'id': 'GW001', 'name': 'North Ridge', 'lat': 45.128, 'lon': -123.451, 'elevation': 1350},
            {'id': 'GW002', 'name': 'South Access', 'lat': 45.118, 'lon': -123.461, 'elevation': 1280},
            {'id': 'GW003', 'name': 'East Monitor', 'lat': 45.123, 'lon': -123.446, 'elevation': 1320},
            {'id': 'GW004', 'name': 'West Platform', 'lat': 45.123, 'lon': -123.466, 'elevation': 1300},
            {'id': 'GW005', 'name': 'Central Hub', 'lat': 45.123, 'lon': -123.456, 'elevation': 1250}
        ]
        
        for gw_pos in gateway_positions:
            gateway = {
                'id': gw_pos['id'],
                'name': gw_pos['name'],
                'coordinates': {
                    'lat': gw_pos['lat'],
                    'lon': gw_pos['lon'], 
                    'elevation': gw_pos['elevation']
                },
                'status': 'online' if np.random.random() > 0.05 else 'offline',
                'signal_strength': np.random.uniform(-60, -40),  # dBm
                'coverage_radius': np.random.uniform(800, 1200),  # meters
                'connected_devices': np.random.randint(8, 15),
                'battery_backup': np.random.uniform(85, 100),  # %
                'last_maintenance': datetime.now() - timedelta(days=np.random.randint(1, 45)),
                'frequency_band': 'EU868' if np.random.random() > 0.5 else 'US915',
                'data_rate': f'SF{np.random.randint(7, 12)}',  # Spreading Factor
                'power_output': np.random.uniform(14, 20)  # dBm
            }
            gateways.append(gateway)
        
        return gateways
    
    def _initialize_devices(self):
        """Initialize LoRaWAN devices (sensors)"""
        devices = []
        
        for i in range(47):  # 47 sensors as per requirements
            device = {
                'id': f"DEV{i+1:03d}",
                'sensor_id': f"S{i+1:03d}",
                'device_type': np.random.choice(['Class A', 'Class B', 'Class C']),
                'connected_gateway': np.random.choice([gw['id'] for gw in self.gateways]),
                'battery_level': np.random.uniform(20, 100),
                'signal_strength': np.random.uniform(-120, -70),  # dBm
                'uplink_count': np.random.randint(1000, 50000),
                'downlink_count': np.random.randint(10, 500),
                'last_seen': datetime.now() - timedelta(minutes=np.random.randint(1, 30)),
                'data_rate': f'SF{np.random.randint(7, 12)}',
                'frequency': np.random.uniform(867.1, 868.5),  # MHz for EU868
                'transmission_power': np.random.randint(2, 14),  # dBm
                'adr_enabled': np.random.choice([True, False]),  # Adaptive Data Rate
                'join_status': 'joined' if np.random.random() > 0.02 else 'joining',
                'packet_loss_rate': np.random.uniform(0, 0.15)
            }
            devices.append(device)
        
        return devices
    
    def _initialize_radio_channels(self):
        """Initialize radio communication channels for backup"""
        channels = []
        
        # VHF channels for emergency communication
        vhf_channels = [
            {'id': 'VHF001', 'frequency': 151.4, 'name': 'Emergency Primary'},
            {'id': 'VHF002', 'frequency': 154.5, 'name': 'Operations'},
            {'id': 'VHF003', 'frequency': 158.7, 'name': 'Maintenance'},
            {'id': 'VHF004', 'frequency': 162.3, 'name': 'Security'}
        ]
        
        # UHF channels for data communication
        uhf_channels = [
            {'id': 'UHF001', 'frequency': 450.2, 'name': 'Data Backup 1'},
            {'id': 'UHF002', 'frequency': 455.8, 'name': 'Data Backup 2'},
            {'id': 'UHF003', 'frequency': 460.1, 'name': 'Telemetry'}
        ]
        
        all_channels = vhf_channels + uhf_channels
        
        for channel in all_channels:
            channel.update({
                'status': 'active' if np.random.random() > 0.1 else 'standby',
                'power_output': np.random.uniform(5, 25),  # Watts
                'range': np.random.uniform(5, 15),  # km
                'noise_level': np.random.uniform(-110, -90),  # dBm
                'modulation': 'FM' if 'VHF' in channel['id'] else 'FSK',
                'bandwidth': 25 if 'VHF' in channel['id'] else 12.5  # kHz
            })
        
        return all_channels
    
    def get_network_status(self):
        """Get current LoRaWAN network status"""
        online_gateways = sum(1 for gw in self.gateways if gw['status'] == 'online')
        total_gateways = len(self.gateways)
        
        connected_devices = sum(1 for dev in self.devices if dev['join_status'] == 'joined')
        total_devices = len(self.devices)
        
        # Calculate average signal strength
        avg_signal = np.mean([gw['signal_strength'] for gw in self.gateways if gw['status'] == 'online'])
        
        # Calculate network coverage
        coverage = (online_gateways / total_gateways) * 0.8 + (connected_devices / total_devices) * 0.2
        
        return {
            'network_type': 'LoRaWAN',
            'coverage': coverage,
            'gateways': online_gateways,
            'total_gateways': total_gateways,
            'devices': connected_devices,
            'total_devices': total_devices,
            'signal_strength': avg_signal,
            'uptime': self.network_status['uptime'],
            'packet_success_rate': 1 - np.mean([dev.get('packet_loss_rate', 0) for dev in self.devices]),
            'gateway_list': [
                {
                    'id': gw['id'],
                    'name': gw['name'],
                    'status': gw['status'],
                    'signal_strength': gw['signal_strength'],
                    'connected_devices': gw['connected_devices']
                }
                for gw in self.gateways
            ]
        }
    
    def get_radio_status(self):
        """Get radio communication backup status"""
        active_channels = [ch for ch in self.radio_channels if ch['status'] == 'active']
        
        if active_channels:
            avg_power = np.mean([ch['power_output'] for ch in active_channels])
            avg_range = np.mean([ch['range'] for ch in active_channels])
            error_rate = np.random.uniform(0.01, 0.05)  # Typical radio error rate
        else:
            avg_power = 0
            avg_range = 0
            error_rate = 1.0
        
        return {
            'communication_type': 'Radio Backup',
            'active_channels': len(active_channels),
            'total_channels': len(self.radio_channels),
            'frequency': np.mean([ch['frequency'] for ch in active_channels]) if active_channels else 0,
            'power': avg_power,
            'range': avg_range,
            'error_rate': error_rate,
            'channel_list': [
                {
                    'id': ch['id'],
                    'name': ch['name'],
                    'frequency': ch['frequency'],
                    'status': ch['status'],
                    'power': ch['power_output']
                }
                for ch in self.radio_channels
            ]
        }
    
    def simulate_data_transmission(self, device_id, data_payload):
        """Simulate data transmission through LoRaWAN"""
        device = next((dev for dev in self.devices if dev['id'] == device_id), None)
        
        if not device:
            return {
                'success': False,
                'error': 'Device not found',
                'timestamp': datetime.now()
            }
        
        # Find connected gateway
        gateway = next((gw for gw in self.gateways if gw['id'] == device['connected_gateway']), None)
        
        if not gateway or gateway['status'] != 'online':
            # Try to find alternative gateway
            online_gateways = [gw for gw in self.gateways if gw['status'] == 'online']
            if online_gateways:
                gateway = min(online_gateways, key=lambda x: np.random.random())  # Simulate closest gateway
                device['connected_gateway'] = gateway['id']
            else:
                return {
                    'success': False,
                    'error': 'No online gateways available',
                    'timestamp': datetime.now()
                }
        
        # Simulate transmission success based on signal strength and other factors
        success_probability = 0.95  # Base success rate
        
        # Reduce success based on signal strength
        if device['signal_strength'] < -110:
            success_probability *= 0.7
        elif device['signal_strength'] < -100:
            success_probability *= 0.85
        
        # Reduce success based on battery level
        if device['battery_level'] < 20:
            success_probability *= 0.8
        
        # Simulate packet loss
        success_probability *= (1 - device.get('packet_loss_rate', 0.05))
        
        transmission_successful = np.random.random() < success_probability
        
        if transmission_successful:
            # Update device statistics
            device['uplink_count'] += 1
            device['last_seen'] = datetime.now()
            
            # Update network statistics
            self.network_status['total_messages'] += 1
            
            return {
                'success': True,
                'gateway_used': gateway['id'],
                'signal_strength': device['signal_strength'],
                'data_rate': device['data_rate'],
                'transmission_time': np.random.uniform(0.1, 2.0),  # seconds
                'timestamp': datetime.now()
            }
        else:
            # Update failure statistics
            self.network_status['failed_messages'] += 1
            
            return {
                'success': False,
                'error': 'Transmission failed',
                'gateway_attempted': gateway['id'],
                'signal_strength': device['signal_strength'],
                'timestamp': datetime.now()
            }
    
    def test_emergency_communication(self):
        """Test emergency communication systems"""
        results = {
            'lorawan_test': False,
            'radio_test': False,
            'satellite_test': False,
            'overall_success': False
        }
        
        # Test LoRaWAN
        online_gateways = [gw for gw in self.gateways if gw['status'] == 'online']
        if len(online_gateways) >= 2:  # Need at least 2 gateways for redundancy
            results['lorawan_test'] = True
        
        # Test Radio
        active_radio_channels = [ch for ch in self.radio_channels if ch['status'] == 'active']
        if len(active_radio_channels) >= 1:
            results['radio_test'] = True
        
        # Simulate satellite backup (always available but with some probability)
        results['satellite_test'] = np.random.random() > 0.05  # 95% availability
        
        # Overall success if at least one communication method works
        results['overall_success'] = any([
            results['lorawan_test'],
            results['radio_test'],
            results['satellite_test']
        ])
        
        return results
    
    def get_device_status(self, device_id):
        """Get detailed status of a specific device"""
        device = next((dev for dev in self.devices if dev['id'] == device_id), None)
        
        if not device:
            return {'error': 'Device not found'}
        
        gateway = next((gw for gw in self.gateways if gw['id'] == device['connected_gateway']), None)
        
        return {
            'device_id': device['id'],
            'sensor_id': device['sensor_id'],
            'status': 'online' if device['join_status'] == 'joined' else 'offline',
            'battery_level': device['battery_level'],
            'signal_strength': device['signal_strength'],
            'connected_gateway': {
                'id': gateway['id'] if gateway else 'None',
                'name': gateway['name'] if gateway else 'None',
                'status': gateway['status'] if gateway else 'offline'
            },
            'communication_stats': {
                'uplink_count': device['uplink_count'],
                'downlink_count': device['downlink_count'],
                'packet_loss_rate': device['packet_loss_rate'],
                'last_seen': device['last_seen']
            },
            'technical_details': {
                'data_rate': device['data_rate'],
                'frequency': device['frequency'],
                'power': device['transmission_power'],
                'adr_enabled': device['adr_enabled']
            }
        }
    
    def simulate_network_failure(self, failure_type='gateway_failure'):
        """Simulate various network failure scenarios"""
        if failure_type == 'gateway_failure':
            # Simulate random gateway failure
            online_gateways = [gw for gw in self.gateways if gw['status'] == 'online']
            if online_gateways:
                failed_gateway = np.random.choice(online_gateways)
                failed_gateway['status'] = 'offline'
                
                # Reassign devices to other gateways
                affected_devices = [dev for dev in self.devices if dev['connected_gateway'] == failed_gateway['id']]
                remaining_gateways = [gw for gw in self.gateways if gw['status'] == 'online']
                
                for device in affected_devices:
                    if remaining_gateways:
                        device['connected_gateway'] = np.random.choice(remaining_gateways)['id']
                    else:
                        device['join_status'] = 'joining'  # No available gateways
        
        elif failure_type == 'interference':
            # Simulate radio interference affecting signal quality
            for device in self.devices:
                device['signal_strength'] -= np.random.uniform(5, 15)
                device['packet_loss_rate'] = min(0.5, device['packet_loss_rate'] + np.random.uniform(0.05, 0.2))
        
        elif failure_type == 'power_outage':
            # Simulate power outage affecting gateways without backup
            for gateway in self.gateways:
                if gateway['battery_backup'] < 50:  # Gateways with low backup
                    gateway['status'] = 'offline'
        
        return {
            'failure_type': failure_type,
            'timestamp': datetime.now(),
            'affected_components': self._count_affected_components()
        }
    
    def _count_affected_components(self):
        """Count affected network components"""
        offline_gateways = sum(1 for gw in self.gateways if gw['status'] == 'offline')
        disconnected_devices = sum(1 for dev in self.devices if dev['join_status'] != 'joined')
        
        return {
            'offline_gateways': offline_gateways,
            'disconnected_devices': disconnected_devices,
            'network_coverage': 1 - (offline_gateways / len(self.gateways))
        }