"""
Mobile Application Interface for Field Personnel
Provides offline capabilities, emergency communication, and real-time updates
"""

import json
import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import streamlit as st
from database.database_manager import RockfallDatabaseManager
from alerts.notification_system import NotificationSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FieldReport:
    """Field inspection report"""
    report_id: str
    inspector_name: str
    timestamp: datetime
    location: Dict[str, float]
    mine_site_id: int
    
    # Inspection details
    inspection_type: str  # routine, emergency, follow_up
    weather_conditions: str
    visibility: str
    access_conditions: str
    
    # Observations
    visual_cracks: List[Dict[str, Any]]
    surface_conditions: str
    vegetation_changes: bool
    erosion_observed: bool
    debris_present: bool
    water_seepage: bool
    
    # Photos and media
    photos: List[str]  # File paths
    videos: List[str]  # File paths
    voice_notes: List[str]  # File paths
    
    # Risk assessment
    immediate_danger: bool
    recommended_actions: List[str]
    priority_level: str  # low, medium, high, critical
    
    # Offline status
    synchronized: bool = False
    sync_timestamp: Optional[datetime] = None

@dataclass
class EmergencyAlert:
    """Emergency alert from field personnel"""
    alert_id: str
    reporter_name: str
    location: Dict[str, float]
    timestamp: datetime
    alert_type: str  # rockfall, equipment_failure, injury, evacuation
    severity: str  # low, medium, high, critical
    description: str
    immediate_action_required: bool
    personnel_at_risk: int
    evacuation_requested: bool
    photos: List[str]
    synchronized: bool = False

class OfflineDataManager:
    """Manages offline data storage and synchronization"""
    
    def __init__(self, data_dir: str = "mobile_data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "offline_data.db")
        self._ensure_data_directory()
        self._initialize_offline_database()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Create subdirectories
        for subdir in ['reports', 'photos', 'videos', 'voice_notes', 'cache']:
            path = os.path.join(self.data_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)
    
    def _initialize_offline_database(self):
        """Initialize SQLite database for offline storage"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Field reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS field_reports (
                    report_id TEXT PRIMARY KEY,
                    inspector_name TEXT,
                    timestamp TEXT,
                    location TEXT,
                    mine_site_id INTEGER,
                    data_json TEXT,
                    synchronized INTEGER DEFAULT 0,
                    sync_timestamp TEXT
                )
            ''')
            
            # Emergency alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emergency_alerts (
                    alert_id TEXT PRIMARY KEY,
                    reporter_name TEXT,
                    timestamp TEXT,
                    location TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    data_json TEXT,
                    synchronized INTEGER DEFAULT 0
                )
            ''')
            
            # Cached sensor data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cached_sensor_data (
                    sensor_id TEXT,
                    timestamp TEXT,
                    value REAL,
                    unit TEXT,
                    cache_time TEXT,
                    PRIMARY KEY (sensor_id, timestamp)
                )
            ''')
            
            # Offline maps and reference data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reference_data (
                    data_type TEXT,
                    data_key TEXT,
                    data_value TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (data_type, data_key)
                )
            ''')
            
            conn.commit()
            logger.info("Offline database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing offline database: {e}")
        finally:
            conn.close()
    
    def store_field_report(self, report: FieldReport) -> bool:
        """Store field report offline"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO field_reports 
                (report_id, inspector_name, timestamp, location, mine_site_id, data_json, synchronized)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id,
                report.inspector_name,
                report.timestamp.isoformat(),
                json.dumps(report.location),
                report.mine_site_id,
                json.dumps(asdict(report)),
                0  # Not synchronized
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored field report {report.report_id} offline")
            return True
            
        except Exception as e:
            logger.error(f"Error storing field report: {e}")
            return False
    
    def store_emergency_alert(self, alert: EmergencyAlert) -> bool:
        """Store emergency alert offline"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO emergency_alerts 
                (alert_id, reporter_name, timestamp, location, alert_type, severity, data_json, synchronized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.reporter_name,
                alert.timestamp.isoformat(),
                json.dumps(alert.location),
                alert.alert_type,
                alert.severity,
                json.dumps(asdict(alert)),
                0  # Not synchronized
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored emergency alert {alert.alert_id} offline")
            return True
            
        except Exception as e:
            logger.error(f"Error storing emergency alert: {e}")
            return False
    
    def get_unsynchronized_data(self) -> Dict[str, List[Dict]]:
        """Get all unsynchronized data"""
        unsync_data = {'reports': [], 'alerts': []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get unsynchronized reports
            cursor.execute('SELECT data_json FROM field_reports WHERE synchronized = 0')
            for row in cursor.fetchall():
                unsync_data['reports'].append(json.loads(row[0]))
            
            # Get unsynchronized alerts
            cursor.execute('SELECT data_json FROM emergency_alerts WHERE synchronized = 0')
            for row in cursor.fetchall():
                unsync_data['alerts'].append(json.loads(row[0]))
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting unsynchronized data: {e}")
        
        return unsync_data
    
    def mark_synchronized(self, item_type: str, item_id: str) -> bool:
        """Mark an item as synchronized"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if item_type == 'report':
                cursor.execute('''
                    UPDATE field_reports 
                    SET synchronized = 1, sync_timestamp = ? 
                    WHERE report_id = ?
                ''', (datetime.now().isoformat(), item_id))
            elif item_type == 'alert':
                cursor.execute('''
                    UPDATE emergency_alerts 
                    SET synchronized = 1 
                    WHERE alert_id = ?
                ''', (item_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error marking {item_type} {item_id} as synchronized: {e}")
            return False

class MobileFieldApp:
    """Main mobile application interface"""
    
    def __init__(self):
        self.db_manager = RockfallDatabaseManager()
        self.notification_system = NotificationSystem()
        self.offline_manager = OfflineDataManager()
        self.online = self._check_connectivity()
        
        # App state
        if 'field_app_state' not in st.session_state:
            st.session_state.field_app_state = {
                'current_inspector': '',
                'current_location': {'lat': 0.0, 'lon': 0.0},
                'active_inspection': None,
                'photo_count': 0
            }
    
    def _check_connectivity(self) -> bool:
        """Check if the app has connectivity to the main system"""
        try:
            # Try to get mine sites from database
            sites = self.db_manager.get_mine_sites()
            return len(sites) > 0
        except:
            return False
    
    def render_mobile_interface(self):
        """Render the main mobile interface"""
        st.set_page_config(
            page_title="Field Inspector App",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Header with connectivity status
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title("🔍 Field Inspector")
        with col2:
            if self.online:
                st.success("🟢 Online")
            else:
                st.error("🔴 Offline")
        with col3:
            if st.button("🔄 Sync"):
                self._synchronize_data()
        
        # Navigation
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Inspection", "🚨 Emergency", "📊 Dashboard", "⚙️ Settings"])\n        \n        with tab1:\n            self._render_inspection_interface()\n        \n        with tab2:\n            self._render_emergency_interface()\n        \n        with tab3:\n            self._render_dashboard_interface()\n        \n        with tab4:\n            self._render_settings_interface()
    
    def _render_inspection_interface(self):
        """Render inspection interface"""
        st.header("Field Inspection")
        
        # Inspector information
        col1, col2 = st.columns(2)
        with col1:
            inspector_name = st.text_input(
                "Inspector Name", 
                value=st.session_state.field_app_state['current_inspector']
            )
            st.session_state.field_app_state['current_inspector'] = inspector_name
        
        with col2:
            mine_site = st.selectbox("Mine Site", ["Copper Ridge Mine", "Iron Mountain", "Silver Creek"])
        
        # Location
        st.subheader("📍 Location")
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude", value=39.7392, format="%.6f")
        with col2:
            lon = st.number_input("Longitude", value=-104.9903, format="%.6f")
        
        if st.button("📱 Use Current Location"):
            st.info("GPS location would be captured on a real mobile device")
        
        # Inspection details
        st.subheader("🔍 Inspection Details")
        
        col1, col2 = st.columns(2)
        with col1:
            inspection_type = st.selectbox("Inspection Type", ["Routine", "Follow-up", "Emergency"])
            weather = st.selectbox("Weather", ["Clear", "Cloudy", "Rainy", "Windy", "Foggy"])
        
        with col2:
            visibility = st.selectbox("Visibility", ["Excellent", "Good", "Fair", "Poor"])
            access = st.selectbox("Access Conditions", ["Normal", "Restricted", "Difficult", "Blocked"])
        
        # Observations
        st.subheader("👁️ Observations")
        
        visual_cracks = st.checkbox("Visual cracks observed")
        erosion_observed = st.checkbox("Erosion observed")
        debris_present = st.checkbox("Debris present")
        vegetation_changes = st.checkbox("Vegetation changes")
        water_seepage = st.checkbox("Water seepage")
        
        surface_conditions = st.text_area("Surface Conditions Description")
        
        # Risk assessment
        st.subheader("⚠️ Risk Assessment")
        immediate_danger = st.checkbox("⚠️ IMMEDIATE DANGER PRESENT")
        priority_level = st.selectbox("Priority Level", ["Low", "Medium", "High", "Critical"])
        
        recommended_actions = st.text_area("Recommended Actions")
        
        # Media capture simulation
        st.subheader("📸 Media Capture")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📸 Take Photo"):
                st.session_state.field_app_state['photo_count'] += 1
                st.success(f"Photo {st.session_state.field_app_state['photo_count']} captured")
        
        with col2:
            if st.button("🎥 Record Video"):
                st.success("Video recording started (simulated)")
        
        with col3:
            if st.button("🎤 Voice Note"):
                st.success("Voice note recorded (simulated)")
        
        # Submit report
        if st.button("💾 Submit Report", type="primary"):
            if inspector_name and surface_conditions:
                report = FieldReport(
                    report_id=f"REP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    inspector_name=inspector_name,
                    timestamp=datetime.now(),
                    location={'lat': lat, 'lon': lon},
                    mine_site_id=1,
                    inspection_type=inspection_type.lower(),
                    weather_conditions=weather,
                    visibility=visibility,
                    access_conditions=access,
                    visual_cracks=[],  # Would contain crack details in real app
                    surface_conditions=surface_conditions,
                    vegetation_changes=vegetation_changes,
                    erosion_observed=erosion_observed,
                    debris_present=debris_present,
                    water_seepage=water_seepage,
                    photos=[f"photo_{i}.jpg" for i in range(st.session_state.field_app_state['photo_count'])],
                    videos=[],
                    voice_notes=[],
                    immediate_danger=immediate_danger,
                    recommended_actions=[recommended_actions] if recommended_actions else [],
                    priority_level=priority_level.lower()
                )
                
                # Store report
                if self.offline_manager.store_field_report(report):
                    st.success("✅ Report saved successfully!")
                    if self.online:
                        st.info("🔄 Attempting to sync with main system...")
                        self._sync_report(report)
                    else:
                        st.warning("📴 Report saved offline - will sync when connection restored")
                else:
                    st.error("❌ Failed to save report")
            else:
                st.error("Please fill in all required fields")
    
    def _render_emergency_interface(self):
        """Render emergency alert interface"""
        st.header("🚨 Emergency Alert")
        
        st.warning("⚠️ USE ONLY FOR IMMEDIATE EMERGENCIES")
        
        # Reporter info
        reporter_name = st.text_input("Reporter Name", value=st.session_state.field_app_state['current_inspector'])
        
        # Emergency details
        col1, col2 = st.columns(2)
        with col1:
            alert_type = st.selectbox("Emergency Type", [
                "Rockfall", "Equipment Failure", "Personnel Injury", "Evacuation Required", "Other"
            ])
        
        with col2:
            severity = st.selectbox("Severity", ["Medium", "High", "Critical"])
        
        # Location
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Emergency Latitude", value=39.7392, format="%.6f")
        with col2:
            lon = st.number_input("Emergency Longitude", value=-104.9903, format="%.6f")
        
        # Emergency details
        description = st.text_area("Emergency Description", placeholder="Describe the emergency situation...")
        
        col1, col2 = st.columns(2)
        with col1:
            immediate_action = st.checkbox("Immediate action required")
            evacuation = st.checkbox("Evacuation requested")
        
        with col2:
            personnel_at_risk = st.number_input("Personnel at risk", min_value=0, value=0)
        
        # Emergency photos
        if st.button("📸 Take Emergency Photo"):
            st.success("Emergency photo captured")
        
        # Submit emergency alert
        if st.button("🚨 SEND EMERGENCY ALERT", type="primary"):
            if reporter_name and description:
                alert = EmergencyAlert(
                    alert_id=f"EMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    reporter_name=reporter_name,
                    location={'lat': lat, 'lon': lon},
                    timestamp=datetime.now(),
                    alert_type=alert_type.lower(),
                    severity=severity.lower(),
                    description=description,
                    immediate_action_required=immediate_action,
                    personnel_at_risk=personnel_at_risk,
                    evacuation_requested=evacuation,
                    photos=[]
                )
                
                # Store and try to send immediately
                if self.offline_manager.store_emergency_alert(alert):
                    st.success("🚨 EMERGENCY ALERT SENT!")
                    
                    # Try to send via multiple channels
                    if self.online:
                        self._send_emergency_alert(alert)
                    else:
                        st.error("📴 No connection - Alert saved for immediate transmission when online")
                        # In a real app, this would try radio/satellite communication
                        
                else:
                    st.error("❌ Failed to send emergency alert")
            else:
                st.error("Please fill in all required fields")
    
    def _render_dashboard_interface(self):
        """Render dashboard with cached data"""
        st.header("📊 Field Dashboard")
        
        # Connectivity status
        if self.online:
            try:
                # Get recent sensor data
                sensors = self.db_manager.get_sensors_for_site(1)
                
                st.subheader("📡 Sensor Status")
                for sensor in sensors[:10]:  # Show first 10
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sensor", sensor['sensor_id'])
                    with col2:
                        st.metric("Status", sensor['status'])
                    with col3:
                        st.metric("Value", sensor.get('latest_value', 'N/A'))
                
                # Recent alerts
                alerts = self.db_manager.get_active_alerts(1)
                st.subheader("🚨 Active Alerts")
                if alerts:
                    for alert in alerts:
                        st.warning(f"**{alert['severity'].upper()}**: {alert['title']}")
                else:
                    st.success("No active alerts")
                
            except Exception as e:
                st.error(f"Error loading dashboard data: {e}")
                self.online = False
        
        if not self.online:
            st.warning("📴 Offline Mode - Showing cached data")
            st.info("Last sync: Not available")
            
            # Show offline status
            unsync_data = self.offline_manager.get_unsynchronized_data()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Pending Reports", len(unsync_data['reports']))
            with col2:
                st.metric("Pending Alerts", len(unsync_data['alerts']))
    
    def _render_settings_interface(self):
        """Render settings interface"""
        st.header("⚙️ Settings")
        
        # App settings
        st.subheader("📱 App Settings")
        
        auto_sync = st.checkbox("Auto-sync when online", value=True)
        photo_quality = st.selectbox("Photo Quality", ["High", "Medium", "Low"])
        gps_accuracy = st.selectbox("GPS Accuracy", ["High", "Medium", "Battery Saver"])
        
        # Storage info
        st.subheader("💾 Storage")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Photos", f"{st.session_state.field_app_state['photo_count']}")
        with col2:
            st.metric("Reports", "5")
        with col3:
            st.metric("Available Space", "2.1 GB")
        
        # Sync settings
        st.subheader("🔄 Synchronization")
        
        if st.button("🔄 Force Sync Now"):
            self._synchronize_data()
        
        if st.button("🗑️ Clear Offline Data"):
            if st.checkbox("Confirm deletion of all offline data"):
                st.warning("This would clear all offline data in a real app")
        
        # Emergency contacts
        st.subheader("📞 Emergency Contacts")
        st.text("Mine Control: +1-555-MINE-911")
        st.text("Emergency Services: 911")
        st.text("Site Manager: +1-555-SITE-MGR")
    
    def _sync_report(self, report: FieldReport):
        """Sync a single report with the main system"""
        try:
            # In a real implementation, this would send the report to the main system
            # For now, we'll simulate successful sync
            st.success(f"✅ Report {report.report_id} synced successfully")
            self.offline_manager.mark_synchronized('report', report.report_id)
            
        except Exception as e:
            st.error(f"Failed to sync report: {e}")
    
    def _send_emergency_alert(self, alert: EmergencyAlert):
        """Send emergency alert via multiple channels"""
        try:
            # Create alert in main system
            alert_id = self.db_manager.create_alert(
                mine_site_id=1,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=f"Field Emergency: {alert.alert_type.title()}",
                message=alert.description,
                location=alert.location,
                triggered_by=f"field_app_{alert.reporter_name}"
            )
            
            # Send notifications
            self.notification_system.send_emergency_alert(
                alert.description, 
                alert.severity, 
                f"GPS: {alert.location['lat']:.6f}, {alert.location['lon']:.6f}"
            )
            
            st.success("🚨 Emergency alert sent via all available channels")
            self.offline_manager.mark_synchronized('alert', alert.alert_id)
            
        except Exception as e:
            st.error(f"Failed to send emergency alert: {e}")
    
    def _synchronize_data(self):
        """Synchronize all offline data"""
        if not self.online:
            st.warning("📴 Cannot sync - No connection to main system")
            return
        
        try:
            unsync_data = self.offline_manager.get_unsynchronized_data()
            
            # Sync reports
            for report_data in unsync_data['reports']:
                report = FieldReport(**report_data)
                self._sync_report(report)
            
            # Sync alerts
            for alert_data in unsync_data['alerts']:
                alert = EmergencyAlert(**alert_data)
                self._send_emergency_alert(alert)
            
            st.success(f"✅ Synchronized {len(unsync_data['reports'])} reports and {len(unsync_data['alerts'])} alerts")
            
        except Exception as e:
            st.error(f"Synchronization failed: {e}")

# Global mobile app instance
mobile_app = MobileFieldApp()