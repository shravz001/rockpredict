import os
import random
import socket
import serial
import threading
import time
from datetime import datetime, timedelta
from twilio.rest import Client

class CommunicationManager:
    def __init__(self):
        self.sms_client = None
        self.email_config = None
        self.lorawan_config = None
        self.radio_config = None
        self.siren_systems = []
        self.communication_log = []
        
        # Initialize communication systems
        self._initialize_systems()
        
        # Start background monitoring
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()
    
    def _initialize_systems(self):
        """Initialize all communication systems"""
        self._initialize_sms()
        self._initialize_email()
        self._initialize_lorawan()
        self._initialize_radio()
        self._initialize_sirens()
    
    def _initialize_sms(self):
        """Initialize SMS service using Twilio"""
        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            phone_number = os.getenv("TWILIO_PHONE_NUMBER")
            
            if account_sid and auth_token and phone_number:
                self.sms_client = Client(account_sid, auth_token)
                self.sms_config = {
                    'phone_number': phone_number,
                    'status': 'Online',
                    'last_test': datetime.now() - timedelta(hours=24),
                    'sent_today': random.randint(0, 15)
                }
            else:
                self.sms_config = {
                    'status': 'Offline - Missing credentials',
                    'last_test': None,
                    'sent_today': 0
                }
        except Exception as e:
            self.sms_config = {
                'status': f'Error - {str(e)}',
                'last_test': None,
                'sent_today': 0
            }
    
    def _initialize_email(self):
        """Initialize email service"""
        self.email_config = {
            'host': os.getenv("EMAIL_HOST", "smtp.gmail.com"),
            'port': int(os.getenv("EMAIL_PORT", "587")),
            'username': os.getenv("EMAIL_USER", ""),
            'password': os.getenv("EMAIL_PASSWORD", ""),
            'status': 'Online' if os.getenv("EMAIL_USER") else 'Offline - Missing credentials',
            'sent_today': random.randint(5, 25),
            'last_sent': '2 hours ago'
        }
    
    def _initialize_lorawan(self):
        """Initialize LoRaWAN communication"""
        self.lorawan_config = {
            'app_key': os.getenv("LORAWAN_APP_KEY", "default_key"),
            'frequency': 868.1,  # MHz (EU frequency)
            'spreading_factor': 7,
            'bandwidth': 125,  # kHz
            'coding_rate': 5,
            'status': 'Online',
            'signal_strength': random.randint(70, 95),
            'active_nodes': random.randint(8, 15),
            'last_heartbeat': datetime.now() - timedelta(minutes=random.randint(1, 10))
        }
        
        # Simulate LoRaWAN network
        self._start_lorawan_simulation()
    
    def _initialize_radio(self):
        """Initialize radio communication system"""
        self.radio_config = {
            'frequency': float(os.getenv("RADIO_FREQUENCY", "462.550")),  # MHz
            'power': 50,  # Watts
            'range': 25,  # km
            'status': 'Online',
            'last_transmission': datetime.now() - timedelta(hours=random.randint(1, 6)),
            'channel': 'Emergency-1'
        }
    
    def _initialize_sirens(self):
        """Initialize emergency siren systems"""
        siren_locations = [
            "North Wall - Zone A",
            "South Wall - Zone B", 
            "East Slope - Zone C",
            "West Slope - Zone D",
            "Central Processing Area",
            "Main Entrance",
            "Equipment Storage"
        ]
        
        for i, location in enumerate(siren_locations):
            siren = {
                'id': f'SIREN_{i+1:03d}',
                'location': location,
                'status': random.choice(['Online', 'Online', 'Online', 'Maintenance']),
                'volume': random.randint(100, 120),  # dB
                'last_test': datetime.now() - timedelta(days=random.randint(1, 7)),
                'battery_backup': random.randint(80, 100)
            }
            self.siren_systems.append(siren)
    
    def _start_lorawan_simulation(self):
        """Start LoRaWAN network simulation"""
        def lorawan_simulation():
            while self.monitoring_active:
                try:
                    # Simulate message transmission
                    if random.random() < 0.1:  # 10% chance per cycle
                        self._log_communication({
                            'type': 'LoRaWAN',
                            'direction': 'Outbound',
                            'recipient': f'Node_{random.randint(1, 15):03d}',
                            'message': 'Sensor data request',
                            'status': 'Sent',
                            'signal_strength': self.lorawan_config['signal_strength']
                        })
                    
                    # Update signal strength
                    self.lorawan_config['signal_strength'] += random.randint(-5, 5)
                    self.lorawan_config['signal_strength'] = max(50, min(100, self.lorawan_config['signal_strength']))
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    print(f"LoRaWAN simulation error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=lorawan_simulation, daemon=True).start()
    
    def _background_monitoring(self):
        """Background monitoring of communication systems"""
        while self.monitoring_active:
            try:
                # Check system health
                self._check_system_health()
                
                # Clean old logs
                self._clean_old_logs()
                
                # Update statistics
                self._update_statistics()
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Communication monitoring error: {e}")
                time.sleep(60)
    
    def _check_system_health(self):
        """Check health of all communication systems"""
        # SMS system health
        if self.sms_client:
            try:
                # Could implement actual Twilio API health check here
                self.sms_config['status'] = 'Online'
            except:
                self.sms_config['status'] = 'Offline'
        
        # LoRaWAN health simulation
        if random.random() < 0.05:  # 5% chance of temporary issues
            self.lorawan_config['status'] = 'Degraded'
        else:
            self.lorawan_config['status'] = 'Online'
        
        # Radio system health
        if random.random() < 0.02:  # 2% chance of issues
            self.radio_config['status'] = 'Offline'
        else:
            self.radio_config['status'] = 'Online'
    
    def send_sms_alert(self, phone_number, message):
        """Send SMS alert"""
        try:
            if self.sms_client and self.sms_config.get('phone_number'):
                message_obj = self.sms_client.messages.create(
                    body=message,
                    from_=self.sms_config['phone_number'],
                    to=phone_number
                )
                
                self._log_communication({
                    'type': 'SMS',
                    'direction': 'Outbound',
                    'recipient': phone_number,
                    'message': message[:50] + '...' if len(message) > 50 else message,
                    'status': 'Sent',
                    'message_sid': message_obj.sid
                })
                
                self.sms_config['sent_today'] += 1
                return {'success': True, 'message_sid': message_obj.sid}
            else:
                raise Exception("SMS service not configured")
                
        except Exception as e:
            self._log_communication({
                'type': 'SMS',
                'direction': 'Outbound',
                'recipient': phone_number,
                'message': message[:50] + '...' if len(message) > 50 else message,
                'status': 'Failed',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    def send_email_alert(self, email_address, subject, message):
        """Send email alert"""
        try:
            # Placeholder for actual email sending implementation
            # Would use smtplib or similar for real implementation
            
            self._log_communication({
                'type': 'Email',
                'direction': 'Outbound',
                'recipient': email_address,
                'message': f"{subject}: {message[:50]}..." if len(message) > 50 else f"{subject}: {message}",
                'status': 'Sent' if self.email_config['status'] == 'Online' else 'Failed'
            })
            
            if self.email_config['status'] == 'Online':
                self.email_config['sent_today'] += 1
                return {'success': True}
            else:
                raise Exception("Email service not available")
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_lorawan_message(self, node_id, payload):
        """Send LoRaWAN message"""
        try:
            # Simulate LoRaWAN transmission
            if self.lorawan_config['status'] == 'Online':
                transmission_time = random.uniform(0.5, 2.0)  # seconds
                
                self._log_communication({
                    'type': 'LoRaWAN',
                    'direction': 'Outbound',
                    'recipient': node_id,
                    'message': f"Payload: {payload[:30]}..." if len(str(payload)) > 30 else f"Payload: {payload}",
                    'status': 'Sent',
                    'transmission_time': transmission_time,
                    'frequency': self.lorawan_config['frequency']
                })
                
                return {'success': True, 'transmission_time': transmission_time}
            else:
                raise Exception("LoRaWAN network unavailable")
                
        except Exception as e:
            self._log_communication({
                'type': 'LoRaWAN',
                'direction': 'Outbound',
                'recipient': node_id,
                'message': f"Payload: {payload}",
                'status': 'Failed',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    def send_radio_message(self, channel, message):
        """Send radio message"""
        try:
            if self.radio_config['status'] == 'Online':
                self._log_communication({
                    'type': 'Radio',
                    'direction': 'Outbound',
                    'recipient': channel,
                    'message': message[:50] + '...' if len(message) > 50 else message,
                    'status': 'Transmitted',
                    'frequency': self.radio_config['frequency'],
                    'power': self.radio_config['power']
                })
                
                self.radio_config['last_transmission'] = datetime.now()
                return {'success': True}
            else:
                raise Exception("Radio system offline")
                
        except Exception as e:
            self._log_communication({
                'type': 'Radio',
                'direction': 'Outbound',
                'recipient': channel,
                'message': message,
                'status': 'Failed',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    def activate_sirens(self, zone=None, message="EMERGENCY ALERT"):
        """Activate emergency sirens"""
        activated_sirens = []
        
        for siren in self.siren_systems:
            if zone is None or zone in siren['location']:
                if siren['status'] == 'Online':
                    self._log_communication({
                        'type': 'Siren',
                        'direction': 'Activation',
                        'recipient': siren['location'],
                        'message': message,
                        'status': 'Activated',
                        'volume': siren['volume']
                    })
                    activated_sirens.append(siren['id'])
        
        return {'activated_sirens': activated_sirens, 'count': len(activated_sirens)}
    
    def test_sirens(self):
        """Test all siren systems"""
        test_results = []
        
        for siren in self.siren_systems:
            if siren['status'] == 'Online':
                # Simulate test
                test_success = random.random() > 0.05  # 95% success rate
                
                result = {
                    'siren_id': siren['id'],
                    'location': siren['location'],
                    'status': 'Pass' if test_success else 'Fail',
                    'volume_measured': siren['volume'] + random.randint(-3, 3)
                }
                
                siren['last_test'] = datetime.now()
                test_results.append(result)
                
                self._log_communication({
                    'type': 'Siren',
                    'direction': 'Test',
                    'recipient': siren['location'],
                    'message': 'System test',
                    'status': 'Pass' if test_success else 'Fail'
                })
        
        return test_results
    
    def get_status(self, mode):
        """Get communication system status"""
        return {
            'sms': {
                'status': self.sms_config['status'],
                'sent_today': self.sms_config['sent_today'],
                'last_sent': '1 hour ago'  # Placeholder
            },
            'email': {
                'status': self.email_config['status'],
                'sent_today': self.email_config['sent_today'],
                'last_sent': self.email_config['last_sent']
            },
            'lorawan': {
                'status': self.lorawan_config['status'],
                'signal_strength': self.lorawan_config['signal_strength'],
                'active_nodes': self.lorawan_config['active_nodes']
            },
            'radio': {
                'status': self.radio_config['status'],
                'frequency': self.radio_config['frequency'],
                'range': self.radio_config['range']
            }
        }
    
    def get_siren_status(self):
        """Get status of all siren systems"""
        return self.siren_systems
    
    def get_backup_status(self):
        """Get backup communication system status"""
        return [
            {
                'name': 'Satellite Phone',
                'status': random.choice(['Online', 'Online', 'Standby']),
                'battery': random.randint(60, 100)
            },
            {
                'name': 'Ham Radio',
                'status': 'Online',
                'frequency': '145.500 MHz'
            },
            {
                'name': 'Emergency Beacon',
                'status': 'Standby',
                'last_test': '3 days ago'
            }
        ]
    
    def get_communication_log(self, message_type="All", time_range="Last 24 Hours", status="All"):
        """Get filtered communication log"""
        filtered_log = self.communication_log.copy()
        
        # Apply type filter
        if message_type != "All":
            filtered_log = [log for log in filtered_log if log['type'] == message_type]
        
        # Apply time filter
        time_filters = {
            "Last Hour": timedelta(hours=1),
            "Last 6 Hours": timedelta(hours=6),
            "Last 24 Hours": timedelta(hours=24),
            "Last Week": timedelta(days=7)
        }
        
        if time_range in time_filters:
            cutoff_time = datetime.now() - time_filters[time_range]
            filtered_log = [log for log in filtered_log if log['timestamp'] > cutoff_time]
        
        # Apply status filter
        if status != "All":
            filtered_log = [log for log in filtered_log if log['status'] == status]
        
        # Sort by timestamp (most recent first)
        filtered_log.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_log
    
    def send_test_message(self, comm_type, message, recipient):
        """Send test message through specified communication type"""
        results = {}
        
        if comm_type == "SMS" or comm_type == "All":
            results['SMS'] = self.send_sms_alert(recipient, f"TEST: {message}")
        
        if comm_type == "Email" or comm_type == "All":
            results['Email'] = self.send_email_alert(recipient, "Test Alert", f"TEST: {message}")
        
        if comm_type == "LoRaWAN" or comm_type == "All":
            results['LoRaWAN'] = self.send_lorawan_message("TEST_NODE", message)
        
        if comm_type == "Radio" or comm_type == "All":
            results['Radio'] = self.send_radio_message("TEST_CHANNEL", f"TEST: {message}")
        
        # Return the first result if testing all, otherwise the specific result
        if comm_type == "All":
            return {'success': any(r.get('success', False) for r in results.values()), 'results': results}
        else:
            return results.get(comm_type, {'success': False, 'error': 'Invalid communication type'})
    
    def _log_communication(self, log_entry):
        """Log communication event"""
        log_entry['timestamp'] = datetime.now()
        log_entry['id'] = len(self.communication_log) + 1
        
        self.communication_log.append(log_entry)
        
        # Keep only last 1000 log entries
        if len(self.communication_log) > 1000:
            self.communication_log = self.communication_log[-1000:]
    
    def _clean_old_logs(self):
        """Clean old log entries"""
        cutoff_time = datetime.now() - timedelta(days=30)
        self.communication_log = [
            log for log in self.communication_log
            if log['timestamp'] > cutoff_time
        ]
    
    def _update_statistics(self):
        """Update communication statistics"""
        # Reset daily counters if new day
        current_date = datetime.now().date()
        
        # This would typically be stored persistently
        # For demo purposes, we'll just update randomly
        if random.random() < 0.1:  # 10% chance to reset (simulating new day)
            self.sms_config['sent_today'] = 0
            self.email_config['sent_today'] = 0
    
    def shutdown(self):
        """Shutdown communication manager"""
        self.monitoring_active = False
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
