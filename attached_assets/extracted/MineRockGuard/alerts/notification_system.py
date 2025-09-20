import os
import json
from datetime import datetime, timedelta
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import numpy as np

class NotificationSystem:
    def __init__(self):
        # Initialize Twilio
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_client = None
        
        if self.twilio_sid and self.twilio_token:
            self.twilio_client = Client(self.twilio_sid, self.twilio_token)
        
        # Initialize SendGrid
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY")
        self.sendgrid_client = None
        
        if self.sendgrid_key:
            self.sendgrid_client = SendGridAPIClient(self.sendgrid_key)
        
        # Alert history
        self.alert_history = []
        self.alert_cooldown = {}  # Prevent spam alerts
        
        # Initialize with some historical alerts
        self._initialize_alert_history()
    
    def _initialize_alert_history(self):
        """Initialize with some sample alert history"""
        base_time = datetime.now()
        
        sample_alerts = [
            {
                'timestamp': base_time - timedelta(hours=2),
                'type': 'High Risk',
                'message': 'Displacement rate exceeded threshold in Zone 3',
                'zone': 'Zone_3',
                'severity': 'high',
                'channels_used': ['email', 'sms'],
                'resolved': True
            },
            {
                'timestamp': base_time - timedelta(hours=8),
                'type': 'Medium Risk',
                'message': 'Increased pore pressure detected in Zone 7',
                'zone': 'Zone_7',
                'severity': 'medium',
                'channels_used': ['email'],
                'resolved': True
            },
            {
                'timestamp': base_time - timedelta(days=1),
                'type': 'Critical',
                'message': 'Emergency: Rock instability detected in Zone 1',
                'zone': 'Zone_1',
                'severity': 'critical',
                'channels_used': ['sms', 'email', 'siren'],
                'resolved': True
            }
        ]
        
        self.alert_history.extend(sample_alerts)
    
    def send_sms_alert(self, phone_number, message):
        """Send SMS alert via Twilio"""
        if not self.twilio_client:
            return {
                'success': False,
                'error': 'Twilio not configured - missing credentials'
            }
        
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone_number
            )
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'message': f'SMS sent successfully to {phone_number}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send SMS: {str(e)}'
            }
    
    def send_email_alert(self, email_address, subject, message, from_email="alerts@mine-safety.com"):
        """Send email alert via SendGrid"""
        if not self.sendgrid_client:
            return {
                'success': False,
                'error': 'SendGrid not configured - missing API key'
            }
        
        try:
            mail = Mail(
                from_email=Email(from_email),
                to_emails=To(email_address),
                subject=subject
            )
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
                <h2>Mine Safety Alert</h2>
                <p><strong>Alert Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Message:</strong> {message}</p>
                <hr>
                <p><em>This is an automated alert from the AI-Based Rockfall Prediction System.</em></p>
                <p>Please take appropriate action as per safety protocols.</p>
            </body>
            </html>
            """
            
            mail.content = Content("text/html", html_content)
            
            response = self.sendgrid_client.send(mail)
            return {
                'success': True,
                'status_code': response.status_code,
                'message': f'Email sent successfully to {email_address}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }
    
    def trigger_audio_siren(self, zone, severity):
        """Simulate audio siren activation"""
        # In a real system, this would interface with physical siren hardware
        siren_patterns = {
            'low': 'Single short beep',
            'medium': '3 short beeps',
            'high': 'Continuous beeping for 30 seconds',
            'critical': 'Emergency evacuation siren - continuous for 2 minutes'
        }
        
        pattern = siren_patterns.get(severity, 'Standard alert')
        
        return {
            'success': True,
            'message': f'Audio siren activated in {zone}',
            'pattern': pattern,
            'duration': '30 seconds' if severity in ['high', 'critical'] else '5 seconds'
        }
    
    def trigger_visual_alert(self, zone, severity):
        """Simulate visual alert system"""
        # In a real system, this would control LED warning lights, displays, etc.
        color_codes = {
            'low': 'Green flashing',
            'medium': 'Yellow flashing',
            'high': 'Orange strobing',
            'critical': 'Red emergency strobing'
        }
        
        visual_pattern = color_codes.get(severity, 'Standard alert')
        
        return {
            'success': True,
            'message': f'Visual alerts activated in {zone}',
            'pattern': visual_pattern,
            'location': f'All display panels in {zone} and surrounding areas'
        }
    
    def send_comprehensive_alert(self, alert_data, phone_number=None, email_address=None, 
                                enable_audio=True, enable_visual=True):
        """Send alert through all configured channels"""
        results = []
        channels_used = []
        
        severity = alert_data.get('severity', 'medium')
        zone = alert_data.get('zone', 'Unknown')
        message = alert_data.get('message', 'Risk threshold exceeded')
        
        # Check cooldown to prevent spam
        cooldown_key = f"{zone}_{severity}"
        now = datetime.now()
        if cooldown_key in self.alert_cooldown:
            if now - self.alert_cooldown[cooldown_key] < timedelta(minutes=15):
                return {
                    'success': False,
                    'error': 'Alert cooldown active - preventing duplicate alerts'
                }
        
        # SMS Alert
        if phone_number and self.twilio_client:
            sms_message = f"MINE ALERT [{severity.upper()}]\n{message}\nZone: {zone}\nTime: {now.strftime('%H:%M')}"
            sms_result = self.send_sms_alert(phone_number, sms_message)
            results.append(('SMS', sms_result))
            if sms_result['success']:
                channels_used.append('sms')
        
        # Email Alert
        if email_address and self.sendgrid_client:
            subject = f"Mine Safety Alert - {severity.upper()} Risk in {zone}"
            email_result = self.send_email_alert(email_address, subject, message)
            results.append(('Email', email_result))
            if email_result['success']:
                channels_used.append('email')
        
        # Audio Siren
        if enable_audio:
            audio_result = self.trigger_audio_siren(zone, severity)
            results.append(('Audio Siren', audio_result))
            if audio_result['success']:
                channels_used.append('siren')
        
        # Visual Alerts
        if enable_visual:
            visual_result = self.trigger_visual_alert(zone, severity)
            results.append(('Visual Alert', visual_result))
            if visual_result['success']:
                channels_used.append('visual')
        
        # Record in history
        alert_record = {
            'timestamp': now,
            'type': alert_data.get('type', 'Risk Alert'),
            'message': message,
            'zone': zone,
            'severity': severity,
            'channels_used': channels_used,
            'resolved': False
        }
        self.alert_history.append(alert_record)
        
        # Set cooldown
        self.alert_cooldown[cooldown_key] = now
        
        return {
            'success': True,
            'message': f'Alert sent via {len(channels_used)} channels',
            'channels_used': channels_used,
            'results': results
        }
    
    def send_test_alert(self, alert_type, phone_number=None, email_address=None, 
                       enable_audio=True, enable_visual=True):
        """Send a test alert"""
        test_alert_data = {
            'type': f'Test {alert_type}',
            'message': f'This is a test {alert_type.lower()} alert from the rockfall prediction system',
            'zone': 'Test_Zone',
            'severity': alert_type.lower().replace(' ', '_')
        }
        
        return self.send_comprehensive_alert(
            test_alert_data, phone_number, email_address, enable_audio, enable_visual
        )
    
    def get_alert_history(self, limit=50):
        """Get recent alert history"""
        return sorted(self.alert_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_alert_statistics(self, days=7):
        """Get alert statistics for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_alerts = [alert for alert in self.alert_history if alert['timestamp'] > cutoff_date]
        
        stats = {
            'total_alerts': len(recent_alerts),
            'by_severity': {},
            'by_zone': {},
            'channels_effectiveness': {}
        }
        
        # Count by severity
        for alert in recent_alerts:
            severity = alert['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Count by zone
        for alert in recent_alerts:
            zone = alert['zone']
            stats['by_zone'][zone] = stats['by_zone'].get(zone, 0) + 1
        
        # Channel effectiveness
        for alert in recent_alerts:
            for channel in alert['channels_used']:
                stats['channels_effectiveness'][channel] = stats['channels_effectiveness'].get(channel, 0) + 1
        
        return stats
    
    def generate_action_plan(self, risk_level, zone_data):
        """Generate automated action plan based on risk level"""
        action_plans = {
            'low': {
                'immediate_actions': [
                    'Continue normal monitoring',
                    'Log incident in daily reports',
                    'Schedule routine inspection within 24 hours'
                ],
                'personnel': 'Shift supervisor',
                'equipment': 'Standard monitoring equipment',
                'timeline': 'Next regular inspection cycle'
            },
            'medium': {
                'immediate_actions': [
                    'Increase monitoring frequency to every 2 hours',
                    'Notify shift supervisor and safety officer',
                    'Restrict non-essential personnel from zone',
                    'Deploy additional sensors if available'
                ],
                'personnel': 'Safety officer, geotechnical engineer',
                'equipment': 'Additional displacement sensors, weather monitoring',
                'timeline': 'Within 2 hours'
            },
            'high': {
                'immediate_actions': [
                    'Evacuate non-essential personnel immediately',
                    'Continuous monitoring - no breaks',
                    'Alert mine manager and emergency response team',
                    'Prepare evacuation routes',
                    'Stop operations in affected zone'
                ],
                'personnel': 'Mine manager, emergency response team, geotechnical specialist',
                'equipment': 'Emergency communication, backup monitoring systems',
                'timeline': 'Immediate - within 30 minutes'
            },
            'critical': {
                'immediate_actions': [
                    'EVACUATE ALL PERSONNEL FROM ZONE IMMEDIATELY',
                    'Sound general alarm',
                    'Contact emergency services',
                    'Implement emergency response protocol',
                    'Stop all operations in mine',
                    'Account for all personnel'
                ],
                'personnel': 'All emergency response personnel, external emergency services',
                'equipment': 'Emergency evacuation equipment, medical support',
                'timeline': 'IMMEDIATE - no delay'
            }
        }
        
        return action_plans.get(risk_level, action_plans['medium'])
