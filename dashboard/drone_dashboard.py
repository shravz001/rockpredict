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
import math

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
        """Render enhanced flight path map with accurate zones"""
        st.subheader("Flight Path & Mine Zone Monitoring")
        
        # Get current position over mine terrain
        current_pos = drone_status.get("current_position", {})
        lat = current_pos.get("lat", 40.5232)  # Bingham Canyon Mine area
        lon = current_pos.get("lon", -112.1500)
        altitude = current_pos.get("altitude", 150)
        
        # Define mine zones with realistic boundaries
        mine_zones = {
            "North Pit": {
                "coords": [[40.5270, -112.1520], [40.5270, -112.1480], [40.5250, -112.1480], [40.5250, -112.1520]],
                "risk_level": "high",
                "color": "rgba(255, 100, 100, 0.3)",
                "border_color": "red",
                "description": "Active mining area - High rockfall risk"
            },
            "South Pit": {
                "coords": [[40.5230, -112.1520], [40.5230, -112.1480], [40.5210, -112.1480], [40.5210, -112.1520]],
                "risk_level": "medium", 
                "color": "rgba(255, 165, 0, 0.3)",
                "border_color": "orange",
                "description": "Secondary mining area - Medium risk"
            },
            "East Bench": {
                "coords": [[40.5250, -112.1480], [40.5250, -112.1460], [40.5220, -112.1460], [40.5220, -112.1480]],
                "risk_level": "low",
                "color": "rgba(255, 255, 0, 0.3)",
                "border_color": "yellow",
                "description": "Stable area - Regular monitoring"
            },
            "West Slope": {
                "coords": [[40.5250, -112.1540], [40.5250, -112.1520], [40.5220, -112.1520], [40.5220, -112.1540]],
                "risk_level": "critical",
                "color": "rgba(139, 0, 0, 0.4)",
                "border_color": "darkred",
                "description": "Unstable slope - Critical monitoring required"
            },
            "Central Monitoring": {
                "coords": [[40.5240, -112.1510], [40.5240, -112.1490], [40.5220, -112.1490], [40.5220, -112.1510]],
                "risk_level": "safe",
                "color": "rgba(0, 255, 0, 0.3)",
                "border_color": "green",
                "description": "Safe zone - Equipment staging area"
            }
        }
        
        # Determine which zone the drone is currently in
        current_zone = self._detect_drone_zone(lat, lon, mine_zones)
        
        # Create enhanced map visualization
        fig = go.Figure()
        
        # Add mine zone boundaries
        for zone_name, zone_data in mine_zones.items():
            zone_coords = zone_data["coords"]
            zone_lats = [coord[0] for coord in zone_coords] + [zone_coords[0][0]]  # Close the polygon
            zone_lons = [coord[1] for coord in zone_coords] + [zone_coords[0][1]]
            
            # Add zone boundary
            fig.add_trace(go.Scattermapbox(
                lat=zone_lats,
                lon=zone_lons,
                mode="lines",
                line=dict(width=3, color=zone_data["border_color"]),
                fill="toself",
                fillcolor=zone_data["color"],
                name=f"{zone_name} ({zone_data['risk_level'].title()})",
                text=zone_data["description"],
                hovertemplate=f"<b>{zone_name}</b><br>Risk Level: {zone_data['risk_level'].title()}<br>{zone_data['description']}<extra></extra>"
            ))
        
        # Add current drone position with enhanced styling
        drone_icon_color = "lime" if current_zone and mine_zones[current_zone]["risk_level"] == "safe" else "red"
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(
                size=20,
                color=drone_icon_color,
                symbol="circle",
                allowoverlap=True
            ),
            text=f"🚁 Drone - {current_zone if current_zone else 'Unknown Zone'}",
            name="Current Drone Position",
            hovertemplate=f"<b>Drone Position</b><br>Zone: {current_zone or 'Unknown'}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}<br>Alt: {altitude}m<extra></extra>"
        ))
        
        # Add flight path with waypoint markers
        if hasattr(self.drone_system, 'flight_path') and self.drone_system.flight_path:
            path_lats = [point.get("lat", 0) for point in self.drone_system.flight_path]
            path_lons = [point.get("lon", 0) for point in self.drone_system.flight_path]
            
            # Flight path line
            fig.add_trace(go.Scattermapbox(
                lat=path_lats,
                lon=path_lons,
                mode="lines",
                line=dict(width=3, color="blue", dash="dash"),
                name="Planned Flight Path",
                hovertemplate="Planned Route<extra></extra>"
            ))
            
            # Waypoint markers
            fig.add_trace(go.Scattermapbox(
                lat=path_lats,
                lon=path_lons,
                mode="markers",
                marker=dict(size=10, color="blue", symbol="circle-open"),
                name="Waypoints",
                text=[f"Waypoint {i+1}" for i in range(len(path_lats))],
                hovertemplate="<b>%{text}</b><br>Lat: %{lat:.6f}<br>Lon: %{lon:.6f}<extra></extra>"
            ))
        
        # Enhanced map layout
        fig.update_layout(
            mapbox=dict(
                style="satellite-streets",  # More detailed satellite view
                center=dict(lat=lat, lon=lon),
                zoom=17  # Closer zoom for detailed zone view
            ),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(
                text=f"Mine Zone Map - Drone Currently in: {current_zone or 'Unknown Zone'}",
                x=0.5,
                xanchor="center"
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left", 
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Enhanced position and zone information
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Zone", current_zone or "Unknown")
            
        with col2:
            if current_zone:
                risk_level = mine_zones[current_zone]["risk_level"]
                risk_colors = {"safe": "🟢", "low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}
                st.metric("Zone Risk", f"{risk_colors.get(risk_level, '⚪')} {risk_level.title()}")
            else:
                st.metric("Zone Risk", "Unknown")
                
        with col3:
            st.metric("Coordinates", f"{lat:.4f}, {lon:.4f}")
            
        with col4:
            st.metric("Altitude AGL", f"{altitude} m")
        
        # Zone details and recommendations
        if current_zone:
            zone_info = mine_zones[current_zone]
            risk_level = zone_info["risk_level"]
            
            if risk_level in ["critical", "high"]:
                st.error(f"⚠️ **HIGH RISK ZONE**: {zone_info['description']}")
                st.write("**Recommendations:** Maintain higher altitude, increase monitoring frequency, be ready for immediate evacuation.")
            elif risk_level == "medium":
                st.warning(f"🟡 **MEDIUM RISK ZONE**: {zone_info['description']}")
                st.write("**Recommendations:** Standard monitoring protocols, maintain safe distance from unstable areas.")
            elif risk_level == "low":
                st.info(f"🟡 **LOW RISK ZONE**: {zone_info['description']}")
                st.write("**Recommendations:** Normal operations, routine monitoring sufficient.")
            else:
                st.success(f"✅ **SAFE ZONE**: {zone_info['description']}")
                st.write("**Recommendations:** Safe for extended operations and close inspection.")
        else:
            st.warning("⚠️ Drone position outside defined monitoring zones. Proceed with caution.")
        
        # Zone statistics
        with st.expander("📊 Zone Coverage Statistics"):
            total_zones = len(mine_zones)
            risk_distribution = {}
            for zone in mine_zones.values():
                risk = zone["risk_level"]
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
                
            st.write(f"**Total Monitoring Zones:** {total_zones}")
            for risk, count in risk_distribution.items():
                percentage = (count / total_zones) * 100
                st.write(f"**{risk.title()} Risk Zones:** {count} ({percentage:.1f}%)")
    
    def _detect_drone_zone(self, lat: float, lon: float, mine_zones: dict) -> str:
        """Detect which zone the drone is currently in using point-in-polygon algorithm"""
        for zone_name, zone_data in mine_zones.items():
            if self._point_in_polygon(lat, lon, zone_data["coords"]):
                return zone_name
        return None
    
    def _point_in_polygon(self, lat: float, lon: float, polygon_coords: list) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = lat, lon
        n = len(polygon_coords)
        inside = False
        
        p1x, p1y = polygon_coords[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon_coords[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
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
    
    def _render_parallel_predictions(self, predictions: Dict[str, Any]):
        """Render parallel predictions from sensors and drone"""
        st.subheader("🎯 Real-Time Risk Assessment")
        
        sensor_pred = predictions.get("sensor_prediction", {})
        drone_pred = predictions.get("drone_prediction", {})
        combined_pred = predictions.get("combined_prediction", {})
        
        # Main combined prediction display
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            risk_level = combined_pred.get("risk_level", "unknown")
            risk_score = combined_pred.get("risk_score", 0.0)
            
            # Color based on risk level
            risk_colors = {
                "low": "green",
                "medium": "orange", 
                "high": "red",
                "critical": "red"
            }
            color = risk_colors.get(risk_level, "gray")
            
            st.markdown(f"""
            ### Combined Risk Assessment
            **Risk Level:** :{color}[{risk_level.upper()}]  
            **Risk Score:** {risk_score:.2f}  
            **Confidence:** {combined_pred.get('confidence', 0):.1%}  
            **Agreement:** {combined_pred.get('agreement', 0):.1%}
            """)
        
        with col2:
            st.metric(
                "Sensor Weight",
                f"{combined_pred.get('sensor_weight', 0):.1%}",
                help="How much the sensor data influences the final prediction"
            )
        
        with col3:
            st.metric(
                "Drone Weight", 
                f"{combined_pred.get('drone_weight', 0):.1%}",
                help="How much the drone analysis influences the final prediction"
            )
        
        # Detailed predictions side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📡 Sensor Prediction")
            if sensor_pred.get("error"):
                st.error(f"Sensor Error: {sensor_pred['error']}")
            else:
                sensor_risk = sensor_pred.get("risk_level", "unknown")
                sensor_color = risk_colors.get(sensor_risk, "gray")
                
                st.markdown(f"""
                **Risk Level:** :{sensor_color}[{sensor_risk.upper()}]  
                **Risk Score:** {sensor_pred.get('risk_score', 0):.2f}  
                **Confidence:** {sensor_pred.get('confidence', 0):.1%}  
                **Active Sensors:** {sensor_pred.get('sensor_count', 0)}  
                **Last Update:** {sensor_pred.get('timestamp', 'Unknown')[-8:]}
                """)
        
        with col2:
            st.markdown("#### 🚁 Drone Analysis")
            if drone_pred.get("error"):
                st.error(f"Drone Error: {drone_pred['error']}")
            else:
                drone_risk = drone_pred.get("risk_level", "unknown")
                drone_color = risk_colors.get(drone_risk, "gray")
                
                st.markdown(f"""
                **Risk Level:** :{drone_color}[{drone_risk.upper()}]  
                **Risk Score:** {drone_pred.get('risk_score', 0):.2f}  
                **Confidence:** {drone_pred.get('confidence', 0):.1%}  
                **Data Source:** {drone_pred.get('data_source', 'Unknown')}  
                **Last Analysis:** {drone_pred.get('last_analysis', 'Never')[-8:] if drone_pred.get('last_analysis') else 'Never'}
                """)
        
        # Risk trend visualization
        if st.checkbox("📊 Show Risk Trend Simulation"):
            self._render_risk_trend_chart(sensor_pred, drone_pred, combined_pred)
    
    def _render_system_status(self, monitoring_status: Dict[str, Any]):
        """Render system monitoring status"""
        st.subheader("🔍 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sensors_active = monitoring_status.get("sensors_active", False)
            status_icon = "🟢" if sensors_active else "🔴"
            st.metric("Sensor Network", f"{status_icon} {'Active' if sensors_active else 'Inactive'}")
        
        with col2:
            drone_active = monitoring_status.get("drone_active", False)
            status_icon = "🟢" if drone_active else "🔴"
            st.metric("Drone System", f"{status_icon} {'Active' if drone_active else 'Inactive'}")
        
        with col3:
            parallel_mode = monitoring_status.get("parallel_mode", False)
            status_icon = "🟢" if parallel_mode else "🟡"
            st.metric("Parallel Mode", f"{status_icon} {'Running' if parallel_mode else 'Standby'}")
    
    def _render_risk_trend_chart(self, sensor_pred: Dict, drone_pred: Dict, combined_pred: Dict):
        """Render simulated risk trend chart"""
        import random
        
        # Generate simulated trend data
        timestamps = [datetime.now() - timedelta(minutes=x) for x in range(30, 0, -1)]
        
        sensor_trend = [max(0, min(1, sensor_pred.get("risk_score", 0.3) + random.uniform(-0.2, 0.2))) for _ in timestamps]
        drone_trend = [max(0, min(1, drone_pred.get("risk_score", 0.3) + random.uniform(-0.2, 0.2))) for _ in timestamps]
        combined_trend = [(s + d) / 2 for s, d in zip(sensor_trend, drone_trend)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=sensor_trend,
            name="Sensor Risk",
            line=dict(color="blue", width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=drone_trend,
            name="Drone Risk", 
            line=dict(color="orange", width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=combined_trend,
            name="Combined Risk",
            line=dict(color="red", width=3)
        ))
        
        fig.update_layout(
            title="Risk Level Trends (Last 30 Minutes)",
            xaxis_title="Time",
            yaxis_title="Risk Score",
            yaxis=dict(range=[0, 1]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_analysis(self, predictions: Dict[str, Any]):
        """Render detailed analysis information"""
        st.subheader("📊 Detailed Analysis")
        
        sensor_pred = predictions.get("sensor_prediction", {})
        drone_pred = predictions.get("drone_prediction", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Sensor Data Analysis")
            if not sensor_pred.get("error"):
                st.json({
                    "risk_level": sensor_pred.get("risk_level"),
                    "risk_score": sensor_pred.get("risk_score"),
                    "confidence": sensor_pred.get("confidence"),
                    "sensor_count": sensor_pred.get("sensor_count"),
                    "data_source": sensor_pred.get("data_source")
                })
            else:
                st.error(sensor_pred.get("error"))
        
        with col2:
            st.markdown("#### Drone Analysis")
            if not drone_pred.get("error"):
                st.json({
                    "risk_level": drone_pred.get("risk_level"),
                    "risk_score": drone_pred.get("risk_score"),
                    "confidence": drone_pred.get("confidence"),
                    "data_source": drone_pred.get("data_source"),
                    "last_analysis": drone_pred.get("last_analysis")
                })
            else:
                st.error(drone_pred.get("error"))
    
    def _render_advanced_controls(self):
        """Render advanced drone control interface"""
        st.subheader("🔧 Advanced Drone Controls")
        
        # Get drone integration status  
        try:
            drone_status = self.drone_integration.get_drone_monitoring_status()
            
            # Status overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Flight Status", "Active" if drone_status.get("drone_status", {}).get("is_active") else "Inactive")
            
            with col2:
                battery = drone_status.get("drone_status", {}).get("battery_level", 0)
                st.metric("Battery Level", f"{battery}%")
            
            with col3:
                backup_mode = drone_status.get("backup_mode_active", False)
                st.metric("Backup Mode", "Active" if backup_mode else "Standby")
            
            with col4:
                last_check = drone_status.get("last_sensor_check")
                if last_check:
                    last_check_str = datetime.fromisoformat(last_check).strftime("%H:%M:%S")
                else:
                    last_check_str = "Never"
                st.metric("Last Sensor Check", last_check_str)
                
            # Mission controls
            st.markdown("#### Mission Controls")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚁 Start Patrol"):
                    result = self.drone_integration.start_routine_patrol()
                    if result["success"]:
                        st.success("Patrol started!")
                        st.rerun()
            
            with col2:
                if st.button("🆘 Emergency Scan"):
                    result = self.drone_integration.check_sensor_status_and_activate_backup()
                    if result["success"]:
                        st.success("Emergency scan initiated!")
                        st.rerun()
            
            with col3:
                if st.button("🏠 Return to Base"):
                    result = self.drone_system.land_drone()
                    if result["success"]:
                        st.success("Returning to base!")
                        st.rerun()
        
        except Exception as e:
            st.error(f"Error loading advanced controls: {e}")
    
    def _render_fallback_dashboard(self):
        """Render fallback dashboard when parallel monitoring fails"""
        st.warning("⚠️ Parallel monitoring unavailable. Showing basic drone controls.")
        
        # Basic drone status
        try:
            drone_status = self.drone_system.get_drone_status()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Drone Status", "Active" if drone_status.get("is_active") else "Inactive")
            with col2:
                st.metric("Battery", f"{drone_status.get('battery_level', 0)}%")
            with col3:
                st.metric("Flight Status", drone_status.get("flight_status", "Unknown"))
            
            # Basic controls
            if st.button("🚁 Activate Drone"):
                self.drone_system.is_active = True
                st.success("Drone activated!")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error in fallback mode: {e}")