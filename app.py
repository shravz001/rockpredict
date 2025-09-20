import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import threading
import json
import os

from data_generator import DataGenerator
from ml_models import RockfallPredictor
from alert_system import AlertSystem
from communication import CommunicationManager
from database import DatabaseManager
from visualizations import Visualizer
from utils import Utils

# Initialize session state
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'data_generator' not in st.session_state:
    st.session_state.data_generator = DataGenerator()
if 'predictor' not in st.session_state:
    st.session_state.predictor = RockfallPredictor()
if 'alert_system' not in st.session_state:
    st.session_state.alert_system = AlertSystem()
if 'comm_manager' not in st.session_state:
    st.session_state.comm_manager = CommunicationManager()
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'visualizer' not in st.session_state:
    st.session_state.visualizer = Visualizer()
if 'utils' not in st.session_state:
    st.session_state.utils = Utils()

def main():
    st.set_page_config(
        page_title="AI Rockfall Prediction System",
        page_icon="⛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏔️ AI-Based Rockfall Prediction and Alert System")
    st.markdown("*Real-time monitoring and prediction for open-pit mine safety*")
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # System status
        st.subheader("System Status")
        if st.session_state.monitoring_active:
            st.success("🟢 Monitoring Active")
            if st.button("🛑 Stop Monitoring"):
                st.session_state.monitoring_active = False
                st.rerun()
        else:
            st.error("🔴 Monitoring Inactive")
            if st.button("▶️ Start Monitoring"):
                st.session_state.monitoring_active = True
                st.rerun()
        
        # Communication settings
        st.subheader("📡 Communication Settings")
        comm_mode = st.selectbox(
            "Communication Mode",
            ["Online", "LoRaWAN", "Radio", "Offline"],
            help="Select communication method for alerts"
        )
        
        # Alert settings
        st.subheader("🚨 Alert Settings")
        risk_threshold = st.slider("Risk Threshold (%)", 0, 100, 75)
        enable_siren = st.checkbox("Enable Emergency Siren", value=True)
        enable_sms = st.checkbox("Enable SMS Alerts", value=True)
        enable_email = st.checkbox("Enable Email Alerts", value=True)
        
        # Mine configuration
        st.subheader("⛏️ Mine Configuration")
        mine_id = st.text_input("Mine ID", value="MINE_001")
        mine_name = st.text_input("Mine Name", value="Sample Open Pit Mine")
        
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Real-time Dashboard", 
        "🗺️ 3D Mine Visualization", 
        "📈 Risk Analytics", 
        "🚨 Alert Management", 
        "📡 Communication Status",
        "⚙️ System Configuration"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_3d_visualization()
    
    with tab3:
        render_analytics()
    
    with tab4:
        render_alert_management()
    
    with tab5:
        render_communication_status(comm_mode)
    
    with tab6:
        render_system_config()

def render_dashboard():
    st.header("📊 Real-time Monitoring Dashboard")
    
    # Generate current sensor data
    current_data = st.session_state.data_generator.generate_realtime_data()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Current risk level
        risk_level = st.session_state.predictor.predict_risk(current_data)
        risk_color = "red" if risk_level > 75 else "orange" if risk_level > 50 else "green"
        st.metric(
            "🎯 Current Risk Level",
            f"{risk_level:.1f}%",
            delta=f"{np.random.uniform(-5, 5):.1f}%"
        )
    
    with col2:
        st.metric(
            "📡 Active Sensors",
            f"{current_data['active_sensors']}/50",
            delta=f"{np.random.randint(-2, 3)}"
        )
    
    with col3:
        st.metric(
            "🌧️ Rainfall (24h)",
            f"{current_data['rainfall_24h']:.1f} mm",
            delta=f"{np.random.uniform(-10, 10):.1f} mm"
        )
    
    with col4:
        st.metric(
            "📊 Stability Index",
            f"{current_data['stability_index']:.2f}",
            delta=f"{np.random.uniform(-0.1, 0.1):.2f}"
        )
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Risk Trend (Last 24 Hours)")
        risk_history = st.session_state.data_generator.generate_risk_history()
        fig_risk = px.line(
            x=risk_history['timestamps'],
            y=risk_history['risk_levels'],
            title="Risk Level Over Time",
            labels={'x': 'Time', 'y': 'Risk Level (%)'}
        )
        fig_risk.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")
        fig_risk.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Medium Risk Threshold")
        st.plotly_chart(fig_risk, width="stretch")
    
    with col2:
        st.subheader("🌡️ Environmental Conditions")
        env_data = st.session_state.data_generator.generate_environmental_data()
        fig_env = go.Figure()
        fig_env.add_trace(go.Scatter(
            x=env_data['timestamps'],
            y=env_data['temperature'],
            name='Temperature (°C)',
            line=dict(color='red')
        ))
        fig_env.add_trace(go.Scatter(
            x=env_data['timestamps'],
            y=env_data['humidity'],
            name='Humidity (%)',
            yaxis='y2',
            line=dict(color='blue')
        ))
        fig_env.update_layout(
            yaxis=dict(title='Temperature (°C)', side='left'),
            yaxis2=dict(title='Humidity (%)', side='right', overlaying='y')
        )
        st.plotly_chart(fig_env, width="stretch")
    
    # Sensor status table
    st.subheader("📊 Sensor Status Overview")
    sensor_data = st.session_state.data_generator.generate_sensor_status()
    df_sensors = pd.DataFrame(sensor_data)
    
    # Color code by status
    def color_status(val):
        if val == 'Online':
            return 'background-color: #90EE90'
        elif val == 'Warning':
            return 'background-color: #FFD700'
        else:
            return 'background-color: #FFB6C1'
    
    styled_df = df_sensors.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, width="stretch")

def render_3d_visualization():
    st.header("🗺️ 3D Mine Visualization")
    
    # Generate 3D mine data
    mine_data = st.session_state.data_generator.generate_3d_mine_data()
    
    # 3D visualization with risk overlay
    fig_3d = st.session_state.visualizer.create_3d_mine_plot(mine_data)
    st.plotly_chart(fig_3d, width="stretch")
    
    # Legend and controls
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎨 Legend")
        st.markdown("""
        **Risk Levels:**
        - 🟢 **Low Risk (0-30%)**: Stable conditions
        - 🟡 **Medium Risk (31-60%)**: Monitor closely
        - 🟠 **High Risk (61-80%)**: Increased vigilance
        - 🔴 **Critical Risk (81-100%)**: Immediate action required
        
        **Sensor Types:**
        - 📏 **Displacement**: Movement detection
        - 🔧 **Strain**: Stress measurement
        - 💧 **Pore Pressure**: Water pressure monitoring
        - 📳 **Vibration**: Seismic activity
        """)
    
    with col2:
        st.subheader("🎛️ Visualization Controls")
        
        # View mode selection
        view_mode = st.selectbox(
            "View Mode",
            ["Risk Overlay", "Sensor Network", "Geological Layers", "Drainage System"]
        )
        
        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            ["Real-time", "Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"]
        )
        
        # Display options
        show_sensors = st.checkbox("Show Sensor Locations", value=True)
        show_risk_zones = st.checkbox("Show Risk Zones", value=True)
        show_terrain = st.checkbox("Show Terrain Model", value=True)
        
        # Generate updated visualization based on controls
        if st.button("🔄 Update Visualization"):
            updated_data = st.session_state.data_generator.generate_3d_mine_data(
                view_mode=view_mode,
                time_range=time_range,
                show_sensors=show_sensors,
                show_risk_zones=show_risk_zones
            )
            fig_updated = st.session_state.visualizer.create_3d_mine_plot(updated_data)
            st.plotly_chart(fig_updated, width="stretch")

def render_analytics():
    st.header("📈 Risk Analytics & Forecasting")
    
    # Prediction model performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Model Performance")
        model_metrics = st.session_state.predictor.get_model_metrics()
        
        metrics_df = pd.DataFrame([
            {"Metric": "Accuracy", "Random Forest": f"{model_metrics['rf_accuracy']:.3f}", "XGBoost": f"{model_metrics['xgb_accuracy']:.3f}"},
            {"Metric": "Precision", "Random Forest": f"{model_metrics['rf_precision']:.3f}", "XGBoost": f"{model_metrics['xgb_precision']:.3f}"},
            {"Metric": "Recall", "Random Forest": f"{model_metrics['rf_recall']:.3f}", "XGBoost": f"{model_metrics['xgb_recall']:.3f}"},
            {"Metric": "F1-Score", "Random Forest": f"{model_metrics['rf_f1']:.3f}", "XGBoost": f"{model_metrics['xgb_f1']:.3f}"}
        ])
        st.dataframe(metrics_df, width="stretch")
    
    with col2:
        st.subheader("🔮 Risk Forecast (Next 48 Hours)")
        forecast_data = st.session_state.predictor.generate_forecast()
        
        fig_forecast = px.line(
            x=forecast_data['timestamps'],
            y=forecast_data['predicted_risk'],
            title="Risk Level Forecast",
            labels={'x': 'Time', 'y': 'Predicted Risk (%)'}
        )
        
        # Add confidence intervals
        fig_forecast.add_trace(go.Scatter(
            x=forecast_data['timestamps'],
            y=forecast_data['upper_bound'],
            fill=None,
            mode='lines',
            line_color='rgba(0,100,80,0)',
            showlegend=False
        ))
        fig_forecast.add_trace(go.Scatter(
            x=forecast_data['timestamps'],
            y=forecast_data['lower_bound'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,100,80,0)',
            name='Confidence Interval',
            fillcolor='rgba(0,100,80,0.2)'
        ))
        
        st.plotly_chart(fig_forecast, width="stretch")
    
    # Feature importance analysis
    st.subheader("🔍 Feature Importance Analysis")
    feature_importance = st.session_state.predictor.get_feature_importance()
    
    fig_importance = px.bar(
        x=feature_importance['importance'],
        y=feature_importance['features'],
        orientation='h',
        title="Feature Importance in Risk Prediction",
        labels={'x': 'Importance Score', 'y': 'Features'}
    )
    st.plotly_chart(fig_importance, width="stretch")
    
    # Historical analysis
    st.subheader("📊 Historical Risk Analysis")
    
    analysis_period = st.selectbox(
        "Analysis Period",
        ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last Year"]
    )
    
    historical_data = st.session_state.data_generator.generate_historical_analysis(analysis_period)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Risk distribution
        fig_dist = px.histogram(
            x=historical_data['risk_levels'],
            nbins=20,
            title="Risk Level Distribution",
            labels={'x': 'Risk Level (%)', 'y': 'Frequency'}
        )
        st.plotly_chart(fig_dist, width="stretch")
    
    with col2:
        # Alert frequency
        fig_alerts = px.bar(
            x=historical_data['alert_dates'],
            y=historical_data['alert_counts'],
            title="Daily Alert Frequency",
            labels={'x': 'Date', 'y': 'Number of Alerts'}
        )
        st.plotly_chart(fig_alerts, width="stretch")
    
    with col3:
        # Correlation matrix
        correlation_data = st.session_state.predictor.get_correlation_matrix()
        fig_corr = px.imshow(
            correlation_data['matrix'],
            x=correlation_data['features'],
            y=correlation_data['features'],
            title="Feature Correlation Matrix",
            aspect="auto"
        )
        st.plotly_chart(fig_corr, width="stretch")

def render_alert_management():
    st.header("🚨 Alert Management System")
    
    # Active alerts
    st.subheader("🔴 Active Alerts")
    active_alerts = st.session_state.alert_system.get_active_alerts()
    
    if active_alerts:
        for alert in active_alerts:
            alert_color = "red" if alert['severity'] == "Critical" else "orange" if alert['severity'] == "High" else "yellow"
            
            with st.container():
                st.markdown(f"""
                <div style="border-left: 5px solid {alert_color}; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
                    <h4>🚨 {alert['title']}</h4>
                    <p><strong>Severity:</strong> {alert['severity']}</p>
                    <p><strong>Location:</strong> {alert['location']}</p>
                    <p><strong>Time:</strong> {alert['timestamp']}</p>
                    <p><strong>Description:</strong> {alert['description']}</p>
                    <p><strong>Recommended Action:</strong> {alert['action']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Acknowledge", key=f"ack_{alert['id']}"):
                        st.session_state.alert_system.acknowledge_alert(alert['id'])
                        st.success("Alert acknowledged")
                        st.rerun()
                
                with col2:
                    if st.button(f"🔄 Escalate", key=f"esc_{alert['id']}"):
                        st.session_state.alert_system.escalate_alert(alert['id'])
                        st.info("Alert escalated")
                        st.rerun()
                
                with col3:
                    if st.button(f"✨ Resolve", key=f"res_{alert['id']}"):
                        st.session_state.alert_system.resolve_alert(alert['id'])
                        st.success("Alert resolved")
                        st.rerun()
    else:
        st.success("✅ No active alerts - All systems normal")
    
    # Alert history
    st.subheader("📋 Alert History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High"]
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now().date() - timedelta(days=7), datetime.now().date()],
            max_value=datetime.now().date()
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status",
            ["All", "Active", "Acknowledged", "Resolved"]
        )
    
    # Get filtered alert history
    alert_history = st.session_state.alert_system.get_alert_history(
        severity_filter=severity_filter,
        date_range=date_range,
        status_filter=status_filter
    )
    
    if alert_history:
        df_alerts = pd.DataFrame(alert_history)
        st.dataframe(df_alerts, width="stretch")
        
        # Alert statistics
        col1, col2 = st.columns(2)
        
        with col1:
            # Alert trends
            daily_alerts = df_alerts.groupby(df_alerts['timestamp'].dt.date).size()
            fig_trends = px.line(
                x=daily_alerts.index,
                y=daily_alerts.values,
                title="Daily Alert Trends",
                labels={'x': 'Date', 'y': 'Number of Alerts'}
            )
            st.plotly_chart(fig_trends, width="stretch")
        
        with col2:
            # Severity distribution
            severity_counts = df_alerts['severity'].value_counts()
            fig_severity = px.pie(
                values=severity_counts.values,
                names=severity_counts.index,
                title="Alert Severity Distribution"
            )
            st.plotly_chart(fig_severity, width="stretch")
    
    # Manual alert creation
    st.subheader("➕ Create Manual Alert")
    with st.expander("Create New Alert"):
        alert_title = st.text_input("Alert Title")
        alert_severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        alert_location = st.text_input("Location (GPS coordinates or zone name)")
        alert_description = st.text_area("Description")
        alert_action = st.text_area("Recommended Action")
        
        if st.button("🚨 Create Alert"):
            if alert_title and alert_description:
                new_alert = {
                    'title': alert_title,
                    'severity': alert_severity,
                    'location': alert_location,
                    'description': alert_description,
                    'action': alert_action,
                    'timestamp': datetime.now(),
                    'status': 'Active',
                    'source': 'Manual'
                }
                st.session_state.alert_system.create_alert(new_alert)
                st.success("Alert created successfully!")
                st.rerun()
            else:
                st.error("Please fill in required fields (Title and Description)")

def render_communication_status(comm_mode):
    st.header("📡 Communication System Status")
    
    # Communication mode status
    st.subheader(f"🔧 Current Mode: {comm_mode}")
    
    comm_status = st.session_state.comm_manager.get_status(comm_mode)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if comm_status['sms']['status'] == 'Online' else "🔴"
        st.metric(
            f"{status_color} SMS Service",
            comm_status['sms']['sent_today'],
            delta=f"Last: {comm_status['sms']['last_sent']}"
        )
    
    with col2:
        status_color = "🟢" if comm_status['email']['status'] == 'Online' else "🔴"
        st.metric(
            f"{status_color} Email Service",
            comm_status['email']['sent_today'],
            delta=f"Last: {comm_status['email']['last_sent']}"
        )
    
    with col3:
        status_color = "🟢" if comm_status['lorawan']['status'] == 'Online' else "🔴"
        st.metric(
            f"{status_color} LoRaWAN",
            f"{comm_status['lorawan']['signal_strength']}%",
            delta=f"Nodes: {comm_status['lorawan']['active_nodes']}"
        )
    
    with col4:
        status_color = "🟢" if comm_status['radio']['status'] == 'Online' else "🔴"
        st.metric(
            f"{status_color} Radio",
            f"{comm_status['radio']['frequency']} MHz",
            delta=f"Range: {comm_status['radio']['range']} km"
        )
    
    # Emergency systems
    st.subheader("🚨 Emergency Systems")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔊 Siren Systems**")
        siren_status = st.session_state.comm_manager.get_siren_status()
        
        for siren in siren_status:
            status_icon = "🟢" if siren['status'] == 'Online' else "🔴"
            st.markdown(f"{status_icon} {siren['location']} - {siren['status']}")
        
        if st.button("🧪 Test All Sirens"):
            st.session_state.comm_manager.test_sirens()
            st.success("Siren test initiated")
    
    with col2:
        st.markdown("**📻 Backup Communication**")
        backup_status = st.session_state.comm_manager.get_backup_status()
        
        for system in backup_status:
            status_icon = "🟢" if system['status'] == 'Online' else "🔴"
            st.markdown(f"{status_icon} {system['name']} - {system['status']}")
    
    # Message log
    st.subheader("📝 Communication Log")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_filter = st.selectbox(
            "Message Type",
            ["All", "SMS", "Email", "LoRaWAN", "Radio", "Siren"]
        )
    
    with col2:
        time_filter = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"]
        )
    
    with col3:
        status_filter_comm = st.selectbox(
            "Status",
            ["All", "Sent", "Failed", "Pending"]
        )
    
    # Get filtered communication log
    comm_log = st.session_state.comm_manager.get_communication_log(
        message_type=log_filter,
        time_range=time_filter,
        status=status_filter_comm
    )
    
    if comm_log:
        df_comm = pd.DataFrame(comm_log)
        st.dataframe(df_comm, width="stretch")
    
    # Test communication
    st.subheader("🧪 Test Communication")
    
    with st.expander("Send Test Message"):
        test_type = st.selectbox(
            "Communication Type",
            ["SMS", "Email", "LoRaWAN", "Radio", "All"]
        )
        test_message = st.text_area("Test Message", value="This is a test message from the rockfall prediction system.")
        test_recipient = st.text_input("Recipient (phone/email)")
        
        if st.button("📤 Send Test"):
            if test_message and test_recipient:
                result = st.session_state.comm_manager.send_test_message(
                    comm_type=test_type,
                    message=test_message,
                    recipient=test_recipient
                )
                if result['success']:
                    st.success(f"Test message sent successfully via {test_type}")
                else:
                    st.error(f"Failed to send test message: {result['error']}")
            else:
                st.error("Please fill in all fields")

def render_system_config():
    st.header("⚙️ System Configuration")
    
    # Model configuration
    st.subheader("🤖 Machine Learning Models")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Random Forest Configuration**")
        rf_n_estimators = st.slider("Number of Estimators", 10, 500, 100)
        rf_max_depth = st.slider("Max Depth", 3, 20, 10)
        rf_min_samples_split = st.slider("Min Samples Split", 2, 20, 2)
        
        if st.button("🔄 Update Random Forest"):
            st.session_state.predictor.update_rf_config({
                'n_estimators': rf_n_estimators,
                'max_depth': rf_max_depth,
                'min_samples_split': rf_min_samples_split
            })
            st.success("Random Forest configuration updated")
    
    with col2:
        st.markdown("**XGBoost Configuration**")
        xgb_n_estimators = st.slider("Number of Estimators", 10, 500, 100, key="xgb_est")
        xgb_max_depth = st.slider("Max Depth", 3, 20, 6, key="xgb_depth")
        xgb_learning_rate = st.slider("Learning Rate", 0.01, 0.3, 0.1, key="xgb_lr")
        
        if st.button("🔄 Update XGBoost"):
            st.session_state.predictor.update_xgb_config({
                'n_estimators': xgb_n_estimators,
                'max_depth': xgb_max_depth,
                'learning_rate': xgb_learning_rate
            })
            st.success("XGBoost configuration updated")
    
    # Data collection settings
    st.subheader("📊 Data Collection Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        collection_interval = st.selectbox(
            "Data Collection Interval",
            ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"]
        )
        
        max_storage_days = st.slider("Max Storage Days", 30, 365, 90)
        
        auto_cleanup = st.checkbox("Auto Cleanup Old Data", value=True)
    
    with col2:
        sensor_timeout = st.slider("Sensor Timeout (seconds)", 30, 300, 60)
        
        data_validation = st.checkbox("Enable Data Validation", value=True)
        
        backup_frequency = st.selectbox(
            "Backup Frequency",
            ["Daily", "Weekly", "Monthly"]
        )
    
    # Database management
    st.subheader("🗄️ Database Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        db_size = st.session_state.db_manager.get_database_size()
        st.metric("Database Size", f"{db_size['size_mb']:.1f} MB")
        
        if st.button("🧹 Cleanup Database"):
            cleanup_result = st.session_state.db_manager.cleanup_old_data()
            st.success(f"Cleaned up {cleanup_result['records_deleted']} old records")
    
    with col2:
        record_count = st.session_state.db_manager.get_record_counts()
        st.metric("Total Records", f"{record_count['total']:,}")
        
        if st.button("📤 Export Data"):
            export_result = st.session_state.db_manager.export_data()
            st.success(f"Data exported to {export_result['filename']}")
    
    with col3:
        last_backup = st.session_state.db_manager.get_last_backup_info()
        st.metric("Last Backup", last_backup['date'])
        
        if st.button("💾 Create Backup"):
            backup_result = st.session_state.db_manager.create_backup()
            st.success(f"Backup created: {backup_result['filename']}")
    
    # System health
    st.subheader("💊 System Health")
    
    health_data = st.session_state.utils.get_system_health()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_color = "red" if health_data['cpu_usage'] > 80 else "orange" if health_data['cpu_usage'] > 60 else "green"
        st.metric("CPU Usage", f"{health_data['cpu_usage']:.1f}%")
    
    with col2:
        memory_color = "red" if health_data['memory_usage'] > 80 else "orange" if health_data['memory_usage'] > 60 else "green"
        st.metric("Memory Usage", f"{health_data['memory_usage']:.1f}%")
    
    with col3:
        disk_color = "red" if health_data['disk_usage'] > 90 else "orange" if health_data['disk_usage'] > 75 else "green"
        st.metric("Disk Usage", f"{health_data['disk_usage']:.1f}%")
    
    with col4:
        network_color = "green" if health_data['network_status'] == 'Connected' else "red"
        st.metric("Network Status", health_data['network_status'])
    
    # Environmental variables
    st.subheader("🔐 Environment Variables")
    
    with st.expander("API Keys and Configuration"):
        st.markdown("""
        **Required Environment Variables:**
        - `TWILIO_ACCOUNT_SID`: Twilio Account SID for SMS
        - `TWILIO_AUTH_TOKEN`: Twilio Auth Token
        - `TWILIO_PHONE_NUMBER`: Twilio Phone Number
        - `EMAIL_HOST`: SMTP Host for email alerts
        - `EMAIL_PORT`: SMTP Port
        - `EMAIL_USER`: Email username
        - `EMAIL_PASSWORD`: Email password
        - `LORAWAN_APP_KEY`: LoRaWAN Application Key
        - `RADIO_FREQUENCY`: Radio frequency for backup communication
        """)
        
        # Check which environment variables are set
        env_vars = {
            'TWILIO_ACCOUNT_SID': bool(os.getenv('TWILIO_ACCOUNT_SID')),
            'TWILIO_AUTH_TOKEN': bool(os.getenv('TWILIO_AUTH_TOKEN')),
            'TWILIO_PHONE_NUMBER': bool(os.getenv('TWILIO_PHONE_NUMBER')),
            'EMAIL_HOST': bool(os.getenv('EMAIL_HOST')),
            'EMAIL_PORT': bool(os.getenv('EMAIL_PORT')),
            'EMAIL_USER': bool(os.getenv('EMAIL_USER')),
            'EMAIL_PASSWORD': bool(os.getenv('EMAIL_PASSWORD')),
            'LORAWAN_APP_KEY': bool(os.getenv('LORAWAN_APP_KEY')),
            'RADIO_FREQUENCY': bool(os.getenv('RADIO_FREQUENCY'))
        }
        
        for var, is_set in env_vars.items():
            status_icon = "✅" if is_set else "❌"
            st.markdown(f"{status_icon} {var}: {'Set' if is_set else 'Not Set'}")

# Background monitoring will be handled differently to avoid session state issues

if __name__ == "__main__":
    main()
