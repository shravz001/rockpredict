import uuid
from datetime import datetime, timedelta
import random
import json

class AlertSystem:
    def __init__(self):
        self.active_alerts = []
        self.alert_history = []
        self.alert_templates = {
            'Critical': {
                'title_prefix': '🚨 CRITICAL ALERT',
                'action_template': 'IMMEDIATE EVACUATION REQUIRED - Clear all personnel from {location}',
                'escalation_delay': 5  # minutes
            },
            'High': {
                'title_prefix': '⚠️ HIGH RISK ALERT',
                'action_template': 'Increase monitoring and prepare for potential evacuation of {location}',
                'escalation_delay': 15
            },
            'Medium': {
                'title_prefix': '⚡ MEDIUM RISK ALERT',
                'action_template': 'Enhanced monitoring required for {location}',
                'escalation_delay': 30
            },
            'Low': {
                'title_prefix': 'ℹ️ LOW RISK ALERT',
                'action_template': 'Continue routine monitoring of {location}',
                'escalation_delay': 60
            }
        }
        
        # Generate some initial sample alerts for demonstration
        self._generate_sample_alerts()
    
    def _generate_sample_alerts(self):
        """Generate sample alerts for demonstration"""
        sample_alerts = [
            {
                'title': 'Elevated Displacement Detected',
                'severity': 'High',
                'location': 'Zone A-3, North Wall',
                'description': 'Displacement sensors show 15mm movement in the last 6 hours, exceeding normal thresholds.',
                'action': 'Restrict access to Zone A-3 and increase monitoring frequency to every 10 minutes.',
                'timestamp': datetime.now() - timedelta(hours=2),
                'status': 'Active',
                'source': 'AI Prediction'
            },
            {
                'title': 'High Pore Pressure Reading',
                'severity': 'Medium',
                'location': 'Zone B-7, East Slope',
                'description': 'Pore pressure levels at 85 kPa, approaching critical threshold after recent rainfall.',
                'action': 'Monitor drainage systems and consider water management interventions.',
                'timestamp': datetime.now() - timedelta(hours=4),
                'status': 'Acknowledged',
                'source': 'Sensor Network'
            }
        ]
        
        for alert_data in sample_alerts:
            alert = self._create_alert_object(alert_data)
            if alert_data['status'] == 'Active':
                self.active_alerts.append(alert)
            else:
                self.alert_history.append(alert)
    
    def _create_alert_object(self, alert_data):
        """Create a standardized alert object"""
        alert_id = str(uuid.uuid4())
        template = self.alert_templates.get(alert_data['severity'], self.alert_templates['Medium'])
        
        alert = {
            'id': alert_id,
            'title': alert_data.get('title', f"{template['title_prefix']} - {alert_data['location']}"),
            'severity': alert_data['severity'],
            'location': alert_data['location'],
            'description': alert_data['description'],
            'action': alert_data.get('action', template['action_template'].format(location=alert_data['location'])),
            'timestamp': alert_data.get('timestamp', datetime.now()),
            'status': alert_data.get('status', 'Active'),
            'source': alert_data.get('source', 'System'),
            'acknowledged_by': alert_data.get('acknowledged_by', None),
            'acknowledged_at': alert_data.get('acknowledged_at', None),
            'resolved_by': alert_data.get('resolved_by', None),
            'resolved_at': alert_data.get('resolved_at', None),
            'escalation_level': 0,
            'escalation_deadline': datetime.now() + timedelta(minutes=template['escalation_delay']),
            'notifications_sent': []
        }
        
        return alert
    
    def create_alert(self, alert_data):
        """Create a new alert"""
        alert = self._create_alert_object(alert_data)
        self.active_alerts.append(alert)
        
        # Send notifications based on severity
        self._send_alert_notifications(alert)
        
        return alert['id']
    
    def acknowledge_alert(self, alert_id, acknowledged_by="System User"):
        """Acknowledge an active alert"""
        for alert in self.active_alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'Acknowledged'
                alert['acknowledged_by'] = acknowledged_by
                alert['acknowledged_at'] = datetime.now()
                return True
        return False
    
    def escalate_alert(self, alert_id, escalated_by="System User"):
        """Escalate an alert to higher severity"""
        for alert in self.active_alerts:
            if alert['id'] == alert_id:
                alert['escalation_level'] += 1
                
                # Increase severity
                severity_levels = ['Low', 'Medium', 'High', 'Critical']
                current_index = severity_levels.index(alert['severity'])
                if current_index < len(severity_levels) - 1:
                    alert['severity'] = severity_levels[current_index + 1]
                
                # Update action and deadline
                template = self.alert_templates[alert['severity']]
                alert['action'] = template['action_template'].format(location=alert['location'])
                alert['escalation_deadline'] = datetime.now() + timedelta(minutes=template['escalation_delay'])
                
                # Send escalated notifications
                self._send_alert_notifications(alert, escalated=True)
                
                return True
        return False
    
    def resolve_alert(self, alert_id, resolved_by="System User", resolution_notes=""):
        """Resolve an active alert"""
        for i, alert in enumerate(self.active_alerts):
            if alert['id'] == alert_id:
                alert['status'] = 'Resolved'
                alert['resolved_by'] = resolved_by
                alert['resolved_at'] = datetime.now()
                alert['resolution_notes'] = resolution_notes
                
                # Move to history
                resolved_alert = self.active_alerts.pop(i)
                self.alert_history.append(resolved_alert)
                
                return True
        return False
    
    def get_active_alerts(self):
        """Get all active alerts, sorted by severity and timestamp"""
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        
        sorted_alerts = sorted(
            self.active_alerts,
            key=lambda x: (severity_order.get(x['severity'], 3), x['timestamp']),
            reverse=True
        )
        
        return sorted_alerts
    
    def get_alert_history(self, severity_filter=None, date_range=None, status_filter="All"):
        """Get filtered alert history"""
        filtered_alerts = self.alert_history.copy()
        
        # Apply severity filter
        if severity_filter:
            filtered_alerts = [alert for alert in filtered_alerts if alert['severity'] in severity_filter]
        
        # Apply date range filter
        if date_range and len(date_range) == 2:
            start_date = datetime.combine(date_range[0], datetime.min.time())
            end_date = datetime.combine(date_range[1], datetime.max.time())
            filtered_alerts = [
                alert for alert in filtered_alerts
                if start_date <= alert['timestamp'] <= end_date
            ]
        
        # Apply status filter
        if status_filter != "All":
            filtered_alerts = [alert for alert in filtered_alerts if alert['status'] == status_filter]
        
        # Sort by timestamp (most recent first)
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_alerts
    
    def _send_alert_notifications(self, alert, escalated=False):
        """Send notifications for an alert (placeholder for actual implementation)"""
        notification_types = []
        
        # Determine notification types based on severity
        if alert['severity'] == 'Critical':
            notification_types = ['SMS', 'Email', 'Radio', 'Siren', 'LoRaWAN']
        elif alert['severity'] == 'High':
            notification_types = ['SMS', 'Email', 'Radio']
        elif alert['severity'] == 'Medium':
            notification_types = ['Email', 'Radio']
        else:
            notification_types = ['Email']
        
        # Add escalation notifications
        if escalated:
            notification_types.extend(['SMS', 'Radio'])
        
        # Record notifications sent
        for notification_type in notification_types:
            alert['notifications_sent'].append({
                'type': notification_type,
                'timestamp': datetime.now(),
                'status': 'Sent',
                'escalated': escalated
            })
    
    def check_escalation_deadlines(self):
        """Check for alerts that need automatic escalation"""
        escalated_alerts = []
        
        for alert in self.active_alerts:
            if (alert['status'] == 'Active' and 
                datetime.now() > alert['escalation_deadline'] and
                alert['escalation_level'] < 3):  # Max 3 escalation levels
                
                if self.escalate_alert(alert['id'], "Auto-Escalation"):
                    escalated_alerts.append(alert['id'])
        
        return escalated_alerts
    
    def get_alert_statistics(self, days=30):
        """Get alert statistics for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get alerts from the specified period
        period_alerts = [
            alert for alert in self.alert_history + self.active_alerts
            if alert['timestamp'] > cutoff_date
        ]
        
        if not period_alerts:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_status': {},
                'avg_resolution_time': 0,
                'escalation_rate': 0
            }
        
        # Calculate statistics
        stats = {
            'total_alerts': len(period_alerts),
            'by_severity': {},
            'by_status': {},
            'avg_resolution_time': 0,
            'escalation_rate': 0
        }
        
        # Count by severity
        for alert in period_alerts:
            severity = alert['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Count by status
        for alert in period_alerts:
            status = alert['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Calculate average resolution time
        resolved_alerts = [alert for alert in period_alerts if alert['status'] == 'Resolved']
        if resolved_alerts:
            resolution_times = []
            for alert in resolved_alerts:
                if alert.get('resolved_at'):
                    resolution_time = (alert['resolved_at'] - alert['timestamp']).total_seconds() / 3600  # hours
                    resolution_times.append(resolution_time)
            
            if resolution_times:
                stats['avg_resolution_time'] = sum(resolution_times) / len(resolution_times)
        
        # Calculate escalation rate
        escalated_alerts = [alert for alert in period_alerts if alert['escalation_level'] > 0]
        stats['escalation_rate'] = (len(escalated_alerts) / len(period_alerts)) * 100 if period_alerts else 0
        
        return stats
    
    def generate_alert_report(self, days=7):
        """Generate a comprehensive alert report"""
        stats = self.get_alert_statistics(days)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_alerts = [
            alert for alert in self.alert_history + self.active_alerts
            if alert['timestamp'] > cutoff_date
        ]
        
        report = {
            'report_period': f"Last {days} days",
            'generated_at': datetime.now(),
            'summary': stats,
            'alerts': recent_alerts,
            'recommendations': self._generate_recommendations(stats, recent_alerts)
        }
        
        return report
    
    def _generate_recommendations(self, stats, alerts):
        """Generate recommendations based on alert patterns"""
        recommendations = []
        
        # High alert frequency
        if stats['total_alerts'] > 20:
            recommendations.append("Consider reviewing sensor thresholds - high alert frequency detected")
        
        # High escalation rate
        if stats['escalation_rate'] > 30:
            recommendations.append("Review alert response procedures - high escalation rate indicates delayed responses")
        
        # Slow resolution times
        if stats['avg_resolution_time'] > 8:
            recommendations.append("Implement faster response protocols - average resolution time exceeds 8 hours")
        
        # Many critical alerts
        critical_count = stats['by_severity'].get('Critical', 0)
        if critical_count > 5:
            recommendations.append("Increase preventive maintenance - multiple critical alerts indicate systemic issues")
        
        # Pattern analysis
        if len(alerts) > 5:
            # Check for recurring locations
            locations = [alert['location'] for alert in alerts]
            location_counts = {}
            for location in locations:
                location_counts[location] = location_counts.get(location, 0) + 1
            
            frequent_locations = [loc for loc, count in location_counts.items() if count > 2]
            if frequent_locations:
                recommendations.append(f"Focus on high-risk areas: {', '.join(frequent_locations)} - recurring alerts detected")
        
        if not recommendations:
            recommendations.append("Alert system operating within normal parameters")
        
        return recommendations
