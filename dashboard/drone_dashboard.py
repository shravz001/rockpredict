"""
Drone Monitoring Dashboard
Real-time monitoring interface for drone operations and image analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from communication.drone_integration import DroneIntegration
from communication.drone_system import DroneSystem

class DroneDashboard:
    """Dashboard for drone monitoring and control"""
    
    def __init__(self):
        if 'drone_integration' not in st.session_state:
            st.session_state.drone_integration = DroneIntegration()
        
        self.drone_integration = st.session_state.drone_integration
        self.drone_system = self.drone_integration.drone_system
    
    def render_drone_monitoring_page(self):
        """Render the main parallel monitoring page"""
        st.title("🚁 Parallel Monitoring System")
        st.markdown("*Real-time predictions from both sensors and drone surveillance*")
        
        # Parallel monitoring controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🚀 Start Parallel Monitoring", type="primary"):
                result = self.drone_integration.start_parallel_monitoring()
                if result.get("success"):
                    st.success("✅ Parallel monitoring activated!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to start: {result.get('message')}")
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        with col3:
            if st.button("⚠️ Emergency Scan"):
                result = self.drone_integration.check_sensor_status_and_activate_backup()
                if result.get("success"):
                    st.success("Emergency scan initiated!")
                    st.rerun()
        
        st.divider()
        
        # Get parallel predictions
        try:
            predictions = self.drone_integration.get_parallel_predictions()
            
            if predictions.get("success") == False:
                st.error(f"Error getting predictions: {predictions.get('message')}")
                return
            
            # Display parallel predictions
            self._render_parallel_predictions(predictions)
            
            st.divider()
            
            # System status overview
            self._render_system_status(predictions.get("monitoring_status", {}))
            
            st.divider()
            
            # Tabs for detailed views
            tabs = st.tabs(["📊 Analysis Details", "🗺️ Flight Map", "⚠️ Alerts", "🔧 Advanced Controls"])
            
            with tabs[0]:
                self._render_detailed_analysis(predictions)
                
            with tabs[1]:
                drone_status = self.drone_system.get_drone_status()
                self._render_flight_map(drone_status)
                
            with tabs[2]:
                self._render_drone_alerts()
                
            with tabs[3]:
                self._render_advanced_controls()
                
        except Exception as e:
            st.error(f"Error loading parallel monitoring dashboard: {str(e)}")
            st.info("Falling back to basic monitoring mode...")
            self._render_fallback_dashboard()
    
    def _render_status_overview(self, drone_status: Dict[str, Any], full_status: Dict[str, Any]):
        """Render drone status overview"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Flight status
        with col1:
            flight_status = drone_status.get("flight_status", "unknown")
            status_icon = {
                "grounded": "🟢",
                "flying": "🔵", 
                "hovering": "🟡",
                "returning": "🟠",
                "emergency": "🔴"
            }.get(flight_status, "⚪")
            
            st.metric("Flight Status", f"{status_icon} {flight_status.title()}")
        
        # Battery level
        with col2:
            battery = drone_status.get("battery_level", 0)
            battery_color = "🔴" if battery < 30 else "🟡" if battery < 60 else "🟢"
            st.metric("Battery Level", f"{battery_color} {battery:.1f}%")
        
        # Backup mode status
        with col3:
            backup_mode = full_status.get("backup_mode_active", False)
            backup_icon = "🚨" if backup_mode else "✅"
            backup_text = "Active" if backup_mode else "Standby"
            st.metric("Backup Mode", f"{backup_icon} {backup_text}")
        
        # Images captured today
        with col4:
            daily_stats = full_status.get("daily_stats", {})
            images_today = daily_stats.get("images_captured_today", 0)
            st.metric("Images Today", f"📸 {images_today}")
        
        # Active alerts
        with col5:
            active_alerts = daily_stats.get("active_alerts", 0)
            alert_icon = "🚨" if active_alerts > 0 else "✅"
            st.metric("Active Alerts", f"{alert_icon} {active_alerts}")
    
    def _render_mission_control(self):
        """Render mission control panel"""
        st.subheader("Mission Control")
        
        drone_status = self.drone_system.get_drone_status()
        is_active = drone_status.get("is_active", False)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚁 Start Patrol", disabled=is_active, use_container_width=True):
                with st.spinner("Starting patrol mission..."):
                    result = self.drone_integration.start_routine_patrol()
                    if result["success"]:
                        st.success("Patrol mission started successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to start patrol: {result['message']}")
        
        with col2:
            if st.button("🆘 Emergency Scan", use_container_width=True):
                with st.spinner("Initiating emergency scan..."):
                    result = self.drone_integration.check_sensor_status_and_activate_backup()
                    if result["success"]:
                        st.success("Emergency scan initiated!")
                        st.rerun()
                    else:
                        st.error(f"Emergency scan failed: {result['message']}")
        
        with col3:
            if st.button("🏠 Return to Base", disabled=not is_active, use_container_width=True):
                with st.spinner("Returning drone to base..."):
                    result = self.drone_system.land_drone()
                    if result["success"]:
                        st.success("Drone returned to base successfully!")
                        st.rerun()
                    else:
                        st.error(f"Return failed: {result['message']}")
        
        # Mission settings
        with st.expander("Mission Settings"):
            st.selectbox("Mission Type", ["patrol", "emergency", "inspection"], index=0)
            st.slider("Flight Altitude (m)", 50, 200, 100)
            st.slider("Image Capture Interval (s)", 5, 60, 15)
            st.checkbox("Auto-return on low battery", value=True)
    
    def _render_quick_stats(self, status: Dict[str, Any]):
        """Render quick statistics panel"""
        st.subheader("Quick Stats")
        
        daily_stats = status.get("daily_stats", {})
        
        # Today's flights
        st.metric("Flights Today", daily_stats.get("flights_today", 0))
        
        # Last sensor check
        last_check = status.get("last_sensor_check")
        if last_check:
            check_time = datetime.fromisoformat(last_check)
            minutes_ago = int((datetime.now() - check_time).total_seconds() / 60)
            st.metric("Last Sensor Check", f"{minutes_ago} min ago")
        
        # System health
        drone_status = status.get("drone_status", {})
        gps_signal = drone_status.get("gps_signal", "unknown")
        comm_link = drone_status.get("communication_link", "unknown")
        
        health_status = "🟢 Good" if gps_signal == "strong" and comm_link == "stable" else "🟡 Fair"
        st.metric("System Health", health_status)
    
    def _render_recent_images(self, recent_analyses: List[Dict[str, Any]]):
        """Render recent captured images"""
        st.subheader("Recent Captured Images")
        
        if not recent_analyses:
            st.info("No recent images captured. Start a patrol mission to begin image capture.")
            return
        
        # Display recent images in a grid
        cols = st.columns(3)
        
        for i, analysis in enumerate(recent_analyses[:6]):  # Show last 6 images
            with cols[i % 3]:
                # Image info card
                timestamp = analysis.get("timestamp", "")
                risk_level = analysis.get("analysis", {}).get("risk_level", "unknown")
                risk_score = analysis.get("analysis", {}).get("risk_score", 0)
                
                risk_color = {
                    "low": "🟢",
                    "medium": "🟡", 
                    "high": "🟠",
                    "critical": "🔴"
                }.get(risk_level, "⚪")
                
                # Create image placeholder (since we're using synthetic images)
                st.markdown(f"""
                <div style="border: 2px solid #ddd; padding: 10px; margin: 5px; border-radius: 10px;">
                    <div style="background: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                        📸 Drone Image
                    </div>
                    <strong>Risk Level:</strong> {risk_color} {risk_level.title()}<br>
                    <strong>Score:</strong> {risk_score:.1f}/100<br>
                    <strong>Time:</strong> {timestamp[:19] if timestamp else 'Unknown'}
                </div>
                """, unsafe_allow_html=True)
    
    def _render_analysis_results(self, recent_analyses: List[Dict[str, Any]]):
        """Render detailed analysis results"""
        st.subheader("Image Analysis Results")
        
        if not recent_analyses:
            st.info("No analysis results available.")
            return
        
        # Create DataFrame for analysis results
        analysis_data = []
        for analysis in recent_analyses:
            analysis_info = analysis.get("analysis", {})
            analysis_data.append({
                "Timestamp": analysis.get("timestamp", "")[:19],
                "Risk Level": analysis_info.get("risk_level", "unknown").title(),
                "Risk Score": analysis_info.get("risk_score", 0),
                "Confidence": f"{analysis_info.get('confidence', 0):.1%}",
                "Features": ", ".join(analysis_info.get("features_detected", [])),
                "Location": f"({analysis.get('location', {}).get('lat', 0):.4f}, {analysis.get('location', {}).get('lon', 0):.4f})"
            })
        
        if analysis_data:
            df = pd.DataFrame(analysis_data)
            st.dataframe(df, use_container_width=True)
            
            # Risk score trend chart
            if len(analysis_data) > 1:
                fig = px.line(df, x="Timestamp", y="Risk Score", 
                             title="Risk Score Trend Over Time",
                             markers=True)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_flight_map(self, drone_status: Dict[str, Any]):
        """Render flight path map"""
        st.subheader("Flight Path & Current Position")
        
        # Get current position
        current_pos = drone_status.get("current_position", {})
        lat = current_pos.get("lat", 39.7392)
        lon = current_pos.get("lon", -104.9903)
        
        # Create map visualization
        fig = go.Figure()
        
        # Add current drone position
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(size=15, color="red"),
            text="Current Drone Position",
            name="Drone"
        ))
        
        # Add flight path if available
        if hasattr(self.drone_system, 'flight_path') and self.drone_system.flight_path:
            path_lats = [point.get("lat", 0) for point in self.drone_system.flight_path]
            path_lons = [point.get("lon", 0) for point in self.drone_system.flight_path]
            
            fig.add_trace(go.Scattermapbox(
                lat=path_lats,
                lon=path_lons,
                mode="markers+lines",
                marker=dict(size=8, color="blue"),
                line=dict(width=2, color="blue"),
                text="Flight Path",
                name="Flight Path"
            ))
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=lat, lon=lon),
                zoom=15
            ),
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Position details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latitude", f"{lat:.6f}")
        with col2:
            st.metric("Longitude", f"{lon:.6f}")
        with col3:
            altitude = current_pos.get("altitude", 0)
            st.metric("Altitude", f"{altitude} m")
    
    def _render_drone_alerts(self):
        """Render drone-specific alerts"""
        st.subheader("Drone Alerts & Notifications")
        
        # This would query the database for drone alerts
        st.info("Drone alert system integrated with main alert management.")
        
        # Sample alert display
        sample_alerts = [
            {
                "timestamp": "2024-01-15 14:30:00",
                "risk_level": "high",
                "message": "High rockfall risk detected in Sector C",
                "location": "Lat: 39.7400, Lon: -104.9910",
                "status": "active"
            }
        ]
        
        for alert in sample_alerts:
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert["risk_level"], "⚪")
            
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #ff4444; padding: 10px; margin: 5px 0; background: #fff5f5;">
                    <strong>{risk_color} {alert["risk_level"].upper()} RISK ALERT</strong><br>
                    <strong>Time:</strong> {alert["timestamp"]}<br>
                    <strong>Location:</strong> {alert["location"]}<br>
                    <strong>Message:</strong> {alert["message"]}<br>
                    <strong>Status:</strong> {alert["status"].title()}
                </div>
                """, unsafe_allow_html=True)
    
    def _render_performance_metrics(self, status: Dict[str, Any]):
        """Render drone performance metrics"""
        st.subheader("Performance Metrics")
        
        daily_stats = status.get("daily_stats", {})
        
        # Performance overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Flight Reliability", "94.2%")
            st.metric("Image Quality Score", "4.7/5.0")
            st.metric("Detection Accuracy", "89.3%")
        
        with col2:
            st.metric("Average Flight Time", "28 min")
            st.metric("Images per Flight", "15.6")
            st.metric("Alert Response Time", "< 2 min")
        
        # Performance charts
        if st.checkbox("Show Detailed Performance Charts"):
            # Sample performance data
            dates = pd.date_range(start="2024-01-01", end="2024-01-15", freq="D")
            performance_data = {
                "Date": dates,
                "Flight Success Rate": [90 + i*0.5 for i in range(len(dates))],
                "Images Captured": [10 + (i % 5) * 3 for i in range(len(dates))],
                "Risk Detections": [2 + (i % 3) for i in range(len(dates))]
            }
            
            df = pd.DataFrame(performance_data)
            
            # Flight success rate chart
            fig1 = px.line(df, x="Date", y="Flight Success Rate", 
                          title="Flight Success Rate Over Time")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Daily activity chart
            fig2 = px.bar(df, x="Date", y=["Images Captured", "Risk Detections"],
                         title="Daily Drone Activity", barmode="group")
            st.plotly_chart(fig2, use_container_width=True)
    
    def render_sensor_backup_status(self):
        """Render sensor backup status component for main dashboard"""
        try:
            # Check sensor status and backup mode
            backup_status = self.drone_integration.check_sensor_status_and_activate_backup()
            
            if backup_status.get("backup_mode", False):
                st.warning("🚨 **SENSOR BACKUP MODE ACTIVE** - Drone monitoring is currently providing coverage for failed sensors.")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Failed Sensors", backup_status.get("failed_sensors", 0))
                with col2:
                    if st.button("View Drone Dashboard"):
                        st.session_state.page = "Drone Monitoring"
                        st.rerun()
            else:
                # Normal operation - show compact status
                drone_status = self.drone_system.get_drone_status()
                if drone_status.get("is_active", False):
                    st.info(f"🚁 Drone active: {drone_status.get('flight_status', 'unknown')} - Battery: {drone_status.get('battery_level', 0):.1f}%")
                
        except Exception as e:
            st.error(f"Error checking drone backup status: {str(e)}")

    def get_drone_status_for_main_dashboard(self) -> Dict[str, Any]:
        """Get drone status data for integration with main dashboard"""
        try:
            status = self.drone_integration.get_drone_monitoring_status()
            drone_status = status.get("drone_status", {})
            
            return {
                "is_active": drone_status.get("is_active", False),
                "flight_status": drone_status.get("flight_status", "grounded"),
                "battery_level": drone_status.get("battery_level", 0),
                "backup_mode_active": status.get("backup_mode_active", False),
                "images_captured_today": status.get("daily_stats", {}).get("images_captured_today", 0),
                "active_alerts": status.get("daily_stats", {}).get("active_alerts", 0)
            }
        except Exception:
            return {
                "is_active": False,
                "flight_status": "error",
                "battery_level": 0,
                "backup_mode_active": False,
                "images_captured_today": 0,
                "active_alerts": 0
            }