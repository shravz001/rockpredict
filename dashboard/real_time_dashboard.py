"""
Real-time dashboard components for the Rockfall Prediction System
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class RealTimeDashboard:
    """Real-time dashboard for monitoring mine conditions"""
    
    def __init__(self):
        self.refresh_interval = 30  # seconds
        
    def render_overview_metrics(self, mine_data):
        """Render key overview metrics"""
        sensors = mine_data.get('sensors', [])
        total_sensors = len(sensors)
        online_sensors = len([s for s in sensors if s.get('status') == 'online'])
        
        # Calculate overall risk level
        risk_levels = [s.get('risk_probability', 0) for s in sensors]
        avg_risk = np.mean(risk_levels) if risk_levels else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Sensors", f"{online_sensors}/{total_sensors}")
        
        with col2:
            risk_color = "red" if avg_risk > 0.7 else "orange" if avg_risk > 0.3 else "green"
            st.metric("Average Risk Level", f"{avg_risk:.1%}")
        
        with col3:
            # Simulate communication status
            comm_status = np.random.uniform(0.85, 0.98)
            st.metric("Communication", f"{comm_status:.1%}")
        
        with col4:
            # Simulate system uptime
            uptime = np.random.uniform(0.95, 0.999)
            st.metric("System Uptime", f"{uptime:.1%}")
    
    def render_risk_timeline(self, prediction_data=None):
        """Render risk timeline chart"""
        if prediction_data is None:
            # Generate sample data
            times = [datetime.now() + timedelta(hours=i) for i in range(24)]
            risks = [0.3 + 0.2 * np.sin(i * np.pi / 12) + np.random.normal(0, 0.1) for i in range(24)]
            risks = [max(0, min(1, r)) for r in risks]
        else:
            times = [p['timestamp'] for p in prediction_data]
            risks = [p['risk_probability'] for p in prediction_data]
        
        fig = go.Figure()
        
        # Risk line
        fig.add_trace(go.Scatter(
            x=times,
            y=risks,
            mode='lines+markers',
            name='Risk Probability',
            line=dict(color='#64748b', width=2),
            marker=dict(size=6)
        ))
        
        # Risk thresholds
        fig.add_hline(y=0.7, line_dash="dash", line_color="red", 
                     annotation_text="High Risk")
        fig.add_hline(y=0.3, line_dash="dash", line_color="yellow", 
                     annotation_text="Medium Risk")
        
        fig.update_layout(
            title="24-Hour Risk Prediction",
            xaxis_title="Time",
            yaxis_title="Risk Probability",
            height=400,
            yaxis=dict(range=[0, 1])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_sensor_status_grid(self, sensors):
        """Render sensor status grid"""
        if not sensors:
            st.warning("No sensor data available")
            return
        
        # Create grid layout
        cols_per_row = 4
        rows = [sensors[i:i + cols_per_row] for i in range(0, len(sensors), cols_per_row)]
        
        for row in rows:
            cols = st.columns(len(row))
            for i, sensor in enumerate(row):
                with cols[i]:
                    status = sensor.get('status', 'unknown')
                    risk = sensor.get('risk_probability', 0)
                    
                    # Determine color based on status and risk
                    if status == 'offline':
                        color = "gray"
                    elif risk > 0.7:
                        color = "red"
                    elif risk > 0.3:
                        color = "orange"
                    else:
                        color = "green"
                    
                    st.markdown(f"""
                    <div style="
                        border: 2px solid {color};
                        padding: 10px;
                        border-radius: 5px;
                        text-align: center;
                        margin: 5px 0;
                    ">
                        <strong>{sensor.get('id', 'Unknown')}</strong><br>
                        Risk: {risk:.1%}<br>
                        Status: {status}
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_communication_status(self, comm_data):
        """Render communication system status"""
        st.subheader("Communication Systems")
        
        if not comm_data:
            st.info("Communication data not available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**LoRaWAN Network**")
            lorawan_status = comm_data.get('lorawan', {})
            
            coverage = lorawan_status.get('coverage', 0.85)
            gateways = lorawan_status.get('gateways', 4)
            devices = lorawan_status.get('devices', 42)
            
            st.metric("Network Coverage", f"{coverage:.1%}")
            st.metric("Active Gateways", gateways)
            st.metric("Connected Devices", devices)
        
        with col2:
            st.write("**Radio Backup**")
            radio_status = comm_data.get('radio', {})
            
            channels = radio_status.get('active_channels', 5)
            error_rate = radio_status.get('error_rate', 0.03)
            
            st.metric("Active Channels", channels)
            st.metric("Error Rate", f"{error_rate:.1%}")
    
    def render_recent_alerts(self, alerts):
        """Render recent alerts panel"""
        st.subheader("Recent Alerts")
        
        if not alerts:
            st.success("No recent alerts")
            return
        
        for alert in alerts[:5]:  # Show last 5 alerts
            severity = alert.get('severity', 'low')
            timestamp = alert.get('timestamp', datetime.now())
            message = alert.get('message', 'Unknown alert')
            zone = alert.get('zone', 'Unknown zone')
            
            # Color coding by severity
            if severity == 'critical':
                color = "red"
            elif severity == 'high':
                color = "orange"
            elif severity == 'medium':
                color = "yellow"
            else:
                color = "green"
            
            with st.expander(f"{severity.upper()} - {zone} ({timestamp.strftime('%H:%M')})"):
                st.write(message)
                if 'channels_used' in alert:
                    st.write(f"Sent via: {', '.join(alert['channels_used'])}")
    
    def render_environmental_conditions(self, env_data):
        """Render environmental conditions"""
        st.subheader("Environmental Conditions")
        
        if not env_data:
            st.info("Environmental data not available")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temp = env_data.get('temperature', 15)
            st.metric("Temperature", f"{temp:.1f}°C")
            
            humidity = env_data.get('humidity', 65)
            st.metric("Humidity", f"{humidity:.0f}%")
        
        with col2:
            wind_speed = env_data.get('wind_speed', 12)
            st.metric("Wind Speed", f"{wind_speed:.1f} m/s")
            
            rainfall = env_data.get('rainfall', 0)
            st.metric("Rainfall", f"{rainfall:.1f} mm/h")
        
        with col3:
            pressure = env_data.get('atmospheric_pressure', 1013)
            st.metric("Pressure", f"{pressure:.0f} hPa")
    
    def render_auto_refresh_control(self):
        """Render auto-refresh controls"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            auto_refresh = st.checkbox("Auto-refresh", value=True)
        
        with col2:
            if st.button("Refresh Now"):
                st.rerun()
        
        if auto_refresh:
            # Auto-refresh every 30 seconds
            st.empty()  # Placeholder for refresh logic
    
    def render_system_status(self, system_stats):
        """Render overall system status"""
        st.subheader("System Status")
        
        if not system_stats:
            st.warning("System statistics not available")
            return
        
        # Status indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Model Performance**")
            accuracy = system_stats.get('model_accuracy', 0.85)
            st.metric("Accuracy", f"{accuracy:.1%}")
            
        with col2:
            st.write("**Data Quality**")
            quality = system_stats.get('data_quality', 0.92)
            st.metric("Data Quality", f"{quality:.1%}")
            
        with col3:
            st.write("**Prediction Confidence**")
            confidence = system_stats.get('prediction_confidence', 0.78)
            st.metric("Confidence", f"{confidence:.1%}")
    
    def render_full_dashboard(self, mine_data, predictions=None, alerts=None, comm_data=None):
        """Render the complete real-time dashboard"""
        st.title("🏔️ Real-Time Mine Monitoring Dashboard")
        
        # Overview metrics
        self.render_overview_metrics(mine_data)
        
        st.divider()
        
        # Main content in columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Risk timeline
            self.render_risk_timeline(predictions)
            
            # Sensor status grid
            st.subheader("Sensor Network Status")
            sensors = mine_data.get('sensors', [])
            self.render_sensor_status_grid(sensors)
        
        with col2:
            # Recent alerts
            self.render_recent_alerts(alerts or [])
            
            # Environmental conditions
            env_data = mine_data.get('environmental', {})
            self.render_environmental_conditions(env_data)
            
            # Communication status
            self.render_communication_status(comm_data)
        
        st.divider()
        
        # System status at bottom
        system_stats = mine_data.get('system_stats', {})
        self.render_system_status(system_stats)
        
        # Auto-refresh controls
        self.render_auto_refresh_control()