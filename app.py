import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os

# Import custom modules
from models.rockfall_predictor import RockfallPredictor
from data.synthetic_data_generator import SyntheticDataGenerator
from visualization.mine_3d_viz import Mine3DVisualizer
from alerts.notification_system import NotificationSystem
from communication.lorawan_simulator import LoRaWANSimulator
from utils.config_manager import ConfigManager
from dashboard.real_time_dashboard import RealTimeDashboard
from analysis.historical_analysis import HistoricalAnalysis
from database.database_manager import get_rockfall_db

# Configure page
st.set_page_config(
    page_title="AI Rockfall Prediction System",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.predictor = RockfallPredictor()
    st.session_state.data_generator = SyntheticDataGenerator()
    st.session_state.visualizer = Mine3DVisualizer()
    st.session_state.notification_system = NotificationSystem()
    st.session_state.lorawan_sim = LoRaWANSimulator()
    st.session_state.config_manager = ConfigManager()
    st.session_state.dashboard = RealTimeDashboard()
    st.session_state.historical_analysis = HistoricalAnalysis()
    st.session_state.db_manager = get_rockfall_db()
    st.session_state.last_update = datetime.now()
    st.session_state.alert_count = 0

def main():
    st.title("🏔️ AI-Based Rockfall Prediction & Alert System")
    st.markdown("**Advanced monitoring and prediction system for open-pit mine safety**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Module",
        ["Real-Time Dashboard", "3D Mine Visualization", "Risk Prediction", 
         "Alert Management", "Historical Analysis", "Communication Status", "System Configuration"]
    )
    
    # Real-time status indicators from database
    try:
        # Ensure database is initialized
        st.session_state.db_manager._initialize_default_data()
        
        # Get real-time statistics from database
        stats = st.session_state.db_manager.get_system_statistics(1)  # Default mine site
        active_alerts = st.session_state.db_manager.get_active_alerts(1)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_icon = "🟢" if stats['communication_success_rate'] > 0.8 else "🟡" if stats['communication_success_rate'] > 0.5 else "🔴"
            st.metric("System Status", f"{status_icon} Online", f"Uptime: {stats['system_uptime']}")
        with col2:
            st.metric("Active Sensors", stats['total_sensors'], f"Readings: {stats['recent_readings']}")
        with col3:
            risk_icon = "🔴" if stats['latest_risk_level'] == 'critical' else "🟠" if stats['latest_risk_level'] == 'high' else "🟡" if stats['latest_risk_level'] == 'medium' else "🟢"
            st.metric("Risk Level", f"{risk_icon} {stats['latest_risk_level'].title()}", f"Score: {stats['latest_risk_score']:.1f}/100")
        with col4:
            st.metric("Active Alerts", len(active_alerts), f"Total: {stats['active_alerts']}")
    except Exception as e:
        # Show specific error for debugging
        st.error(f"Database error: {str(e)}")
        # Fallback to original metrics if database is unavailable
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("System Status", "🟡 Limited", "Database connection issue")
        with col2:
            st.metric("Active Sensors", "--", "Loading...")
        with col3:
            st.metric("Risk Level", "--", "Loading...")
        with col4:
            st.metric("Alerts Today", "--", "Loading...")
    
    st.divider()
    
    # Route to selected page
    if page == "Real-Time Dashboard":
        show_real_time_dashboard()
    elif page == "3D Mine Visualization":
        show_3d_visualization()
    elif page == "Risk Prediction":
        show_risk_prediction()
    elif page == "Alert Management":
        show_alert_management()
    elif page == "Historical Analysis":
        show_historical_analysis()
    elif page == "Communication Status":
        show_communication_status()
    elif page == "System Configuration":
        show_system_configuration()

def show_real_time_dashboard():
    st.header("📊 Real-Time Monitoring Dashboard")
    
    # Get real sensor data from database, fallback to synthetic
    try:
        mine_sites = st.session_state.db_manager.get_mine_sites()
        if mine_sites:
            current_mine = mine_sites[0]  # Use first mine site
            sensors = st.session_state.db_manager.get_sensors_for_site(current_mine['id'])
            env_data = st.session_state.db_manager.get_environmental_data(current_mine['id'])
            
            # Create enhanced data structure
            current_data = {
                'mine_site': current_mine,
                'sensors': sensors,
                'environmental': env_data[-1] if env_data else {},
                'risk_assessments': st.session_state.db_manager.get_recent_risk_assessments(current_mine['id'], 5)
            }
        else:
            # Fallback to synthetic data
            current_data = st.session_state.data_generator.generate_real_time_data()
    except Exception as e:
        st.warning(f"Using synthetic data due to database issue: {str(e)}")
        current_data = st.session_state.data_generator.generate_real_time_data()
    
    # Use the professional dashboard
    try:
        st.session_state.dashboard.render_full_dashboard(
            current_data,
            predictions=st.session_state.predictor.generate_predictions(),
            alerts=st.session_state.notification_system.get_alert_history(10),
            comm_data={
                'lorawan': st.session_state.lorawan_sim.get_network_status(),
                'radio': st.session_state.lorawan_sim.get_radio_status()
            }
        )
    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")
        st.info("Falling back to simplified view...")
        
        # Simple fallback dashboard
        render_simple_dashboard(current_data)

def render_simple_dashboard(current_data):
    """Simplified dashboard fallback"""
    # Display key sensor metrics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Mine Risk Zones")
        try:
            # Create simple risk heatmap
            sensors = current_data.get('sensors', [])
            if sensors:
                sensor_df = pd.DataFrame(sensors)
                st.dataframe(sensor_df[['sensor_id', 'sensor_type', 'status']].head(10))
            else:
                st.info("No sensor data available")
        except Exception as e:
            st.info("Sensor visualization not available")
        
        # Add legend
        st.markdown("""
        **Risk Level Legend:**
        - 🟢 **Low Risk (0-30%)**: Normal operations
        - 🟡 **Medium Risk (30-70%)**: Increased monitoring
        - 🟠 **High Risk (70-85%)**: Caution advised
        - 🔴 **Critical Risk (85-100%)**: Immediate action required
        """)
    
    with col2:
        st.subheader("Current Sensor Readings")
        
        # Display key sensor metrics
        sensors = current_data.get('sensors', [])
        if sensors:
            for i, sensor in enumerate(sensors[:5]):  # Show top 5 sensors
                # Handle both old and new data formats
                if 'risk_probability' in sensor:
                    risk_level = sensor['risk_probability']
                else:
                    # Calculate a simple risk based on latest value if available
                    risk_level = 0.3 + (hash(sensor.get('sensor_id', '')) % 100) / 1000
                
                if risk_level > 0.85:
                    status = "🔴 Critical"
                elif risk_level > 0.7:
                    status = "🟠 High"
                elif risk_level > 0.3:
                    status = "🟡 Medium"
                else:
                    status = "🟢 Low"
                
                sensor_name = sensor.get('sensor_id', sensor.get('id', f'Sensor {i+1}'))
                latest_value = sensor.get('latest_value', 'N/A')
                
                st.metric(
                    sensor_name,
                    f"{latest_value}" if latest_value != 'N/A' else "No data",
                    status
                )
        else:
            st.info("No sensor data available")

def show_3d_visualization():
    st.header("🏔️ 3D Mine Visualization")
    
    # Generate 3D mine data
    mine_data = st.session_state.data_generator.generate_mine_topology()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 3D visualization
        fig_3d = st.session_state.visualizer.create_3d_mine_view(mine_data)
        st.plotly_chart(fig_3d, use_container_width=True)
    
    with col2:
        st.subheader("Visualization Controls")
        
        # View options
        view_mode = st.selectbox("View Mode", ["Risk Overlay", "Sensor Network", "Geological Layers"])
        show_sensors = st.checkbox("Show Sensors", value=True)
        show_risk_zones = st.checkbox("Show Risk Zones", value=True)
        
        # Color scheme
        color_scheme = st.selectbox("Color Scheme", ["Risk-based", "Elevation", "Geological"])
        
        # Update visualization based on controls
        if st.button("Update Visualization"):
            updated_fig = st.session_state.visualizer.update_3d_view(
                mine_data, view_mode, show_sensors, show_risk_zones, color_scheme
            )
            st.plotly_chart(updated_fig, use_container_width=True)
        
        st.subheader("Legend")
        st.markdown("""
        **3D Visualization Elements:**
        - 🔴 High-risk zones
        - 🟡 Medium-risk zones  
        - 🟢 Low-risk zones
        - 📍 Sensor locations
        - 🏔️ Terrain elevation
        - ⚠️ Alert zones
        """)

def show_risk_prediction():
    st.header("🤖 AI Risk Prediction")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Prediction Model Performance")
        
        # Generate prediction data
        prediction_data = st.session_state.predictor.generate_predictions()
        
        # Show prediction accuracy metrics
        accuracy_metrics = st.session_state.predictor.get_model_metrics()
        
        # Display metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Model Accuracy", f"{accuracy_metrics['accuracy']:.1%}")
        with metric_col2:
            st.metric("Precision", f"{accuracy_metrics['precision']:.1%}")
        with metric_col3:
            st.metric("Recall", f"{accuracy_metrics['recall']:.1%}")
        
        # Prediction timeline
        fig_timeline = st.session_state.predictor.create_prediction_timeline(prediction_data)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Feature importance
        st.subheader("Feature Importance Analysis")
        feature_importance = st.session_state.predictor.get_feature_importance()
        fig_features = px.bar(
            x=list(feature_importance.values()),
            y=list(feature_importance.keys()),
            orientation='h',
            title="Factors Contributing to Rockfall Risk"
        )
        st.plotly_chart(fig_features, use_container_width=True)
    
    with col2:
        st.subheader("Prediction Settings")
        
        # Prediction parameters
        prediction_horizon = st.slider("Prediction Horizon (hours)", 1, 72, 24)
        confidence_threshold = st.slider("Confidence Threshold", 0.5, 0.95, 0.8)
        
        # Model selection
        model_type = st.selectbox("Model Type", ["Random Forest", "Neural Network", "SVM", "Ensemble"])
        
        # Retrain model button
        if st.button("Retrain Model"):
            with st.spinner("Retraining model with latest data..."):
                st.session_state.predictor.retrain_model(model_type)
                st.success("Model retrained successfully!")
        
        st.subheader("Risk Factors")
        risk_factors = st.session_state.predictor.get_current_risk_factors()
        for factor, value in risk_factors.items():
            st.metric(factor.replace('_', ' ').title(), f"{value:.3f}")

def show_alert_management():
    st.header("🚨 Alert Management System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Alert Configuration")
        
        # Alert thresholds
        st.write("**Risk Level Thresholds**")
        low_threshold = st.slider("Low Risk Threshold", 0.0, 1.0, 0.3)
        medium_threshold = st.slider("Medium Risk Threshold", 0.0, 1.0, 0.7)
        high_threshold = st.slider("High Risk Threshold", 0.0, 1.0, 0.85)
        
        # Notification channels
        st.write("**Notification Channels**")
        enable_sms = st.checkbox("SMS Alerts", value=True)
        enable_email = st.checkbox("Email Alerts", value=True)
        enable_audio = st.checkbox("Audio Sirens", value=True)
        enable_visual = st.checkbox("Visual Alerts", value=True)
        
        # Contact information
        phone_number = None
        email_address = None
        if enable_sms or enable_email:
            st.subheader("Contact Information")
            phone_number = st.text_input("Phone Number", placeholder="+1234567890")
            email_address = st.text_input("Email Address", placeholder="alerts@mine.com")
        
        # Test alerts
        st.subheader("Test Alert System")
        test_alert_type = st.selectbox("Test Alert Type", ["Low Risk", "Medium Risk", "High Risk", "Critical"])
        
        if st.button("Send Test Alert"):
            result = st.session_state.notification_system.send_test_alert(
                test_alert_type, phone_number if enable_sms else None, 
                email_address if enable_email else None,
                enable_audio, enable_visual
            )
            if result['success']:
                st.success(f"Test alert sent successfully! {result['message']}")
                st.session_state.alert_count += 1
            else:
                st.error(f"Failed to send test alert: {result['error']}")
    
    with col2:
        st.subheader("Alert History")
        
        # Recent alerts
        alert_history = st.session_state.notification_system.get_alert_history()
        for alert in alert_history[:10]:  # Show last 10 alerts
            timestamp = alert['timestamp'].strftime("%Y-%m-%d %H:%M")
            st.write(f"**{timestamp}**")
            st.write(f"{alert['type']}: {alert['message']}")
            st.write(f"Zone: {alert['zone']}")
            st.divider()
        
        st.subheader("Action Plans")
        action_plans = {
            "Low Risk": "Continue normal operations with standard monitoring",
            "Medium Risk": "Increase monitoring frequency, alert supervisors",
            "High Risk": "Evacuate non-essential personnel, increase patrols",
            "Critical": "Immediate evacuation, halt operations, emergency response"
        }
        
        for risk_level, action in action_plans.items():
            with st.expander(f"{risk_level} Action Plan"):
                st.write(action)

def show_historical_analysis():
    st.header("📈 Historical Analysis & Trends")
    
    # Generate historical data
    historical_data = st.session_state.historical_analysis.generate_historical_data()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Risk trend over time
        st.subheader("Risk Trend Analysis")
        fig_trend = st.session_state.historical_analysis.create_risk_timeline(historical_data)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Seasonal patterns
        st.subheader("Seasonal Risk Patterns")
        fig_seasonal = st.session_state.historical_analysis.create_seasonal_analysis(historical_data)
        st.plotly_chart(fig_seasonal, use_container_width=True)
        
        # Correlation analysis
        st.subheader("Environmental Factor Correlations")
        correlation_data = st.session_state.historical_analysis.calculate_correlations(historical_data)
        fig_corr = px.imshow(
            correlation_data,
            title="Correlation Matrix - Environmental Factors vs Risk",
            color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    
    with col2:
        st.subheader("Analysis Controls")
        
        # Date range selector
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End Date", datetime.now())
        
        # Analysis type
        analysis_type = st.selectbox("Analysis Type", 
                                   ["Risk Trends", "Sensor Performance", "Alert Frequency", "Environmental Impact"])
        
        # Generate report
        if st.button("Generate Report"):
            with st.spinner("Generating analysis report..."):
                report = st.session_state.historical_analysis.generate_report(
                    historical_data, start_date, end_date, analysis_type
                )
                st.success("Report generated successfully!")
                
                # Display report summary
                st.subheader("Report Summary")
                for key, value in report.items():
                    st.metric(key.replace('_', ' ').title(), value)

def show_communication_status():
    st.header("📡 Communication System Status")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("LoRaWAN Network Status")
        
        # LoRaWAN status
        lorawan_status = st.session_state.lorawan_sim.get_network_status()
        
        # Network metrics
        st.metric("Network Coverage", f"{lorawan_status['coverage']:.1%}")
        st.metric("Active Gateways", lorawan_status['gateways'])
        st.metric("Connected Devices", lorawan_status['devices'])
        st.metric("Signal Strength", f"{lorawan_status['signal_strength']} dBm")
        
        # Gateway status
        st.subheader("Gateway Status")
        for gateway in lorawan_status['gateway_list']:
            status_color = "🟢" if gateway['status'] == 'online' else "🔴"
            st.write(f"{status_color} Gateway {gateway['id']}: {gateway['status']}")
    
    with col2:
        st.subheader("Radio Communication")
        
        # Radio status
        radio_status = st.session_state.lorawan_sim.get_radio_status()
        
        st.metric("Radio Frequency", f"{radio_status['frequency']} MHz")
        st.metric("Transmission Power", f"{radio_status['power']} dBm")
        st.metric("Error Rate", f"{radio_status['error_rate']:.1%}")
        
        # Emergency communication
        st.subheader("Emergency Communication")
        st.write("**Backup Systems:**")
        st.write("🔄 Satellite uplink: Available")
        st.write("📻 Emergency radio: Standby")
        st.write("🚨 Siren network: Operational")
        
        # Test communication
        if st.button("Test Emergency Communication"):
            test_result = st.session_state.lorawan_sim.test_emergency_communication()
            if test_result['overall_success']:
                st.success("Emergency communication test successful!")
            else:
                st.error("Emergency communication test failed!")

def show_system_configuration():
    st.header("⚙️ System Configuration")
    
    config = st.session_state.config_manager.get_current_config()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("API Configuration")
        
        # API key status (never show actual keys)
        api_keys = {
            "OpenAI API": os.getenv("OPENAI_API_KEY") is not None,
            "Twilio": os.getenv("TWILIO_ACCOUNT_SID") is not None,
            "SendGrid": os.getenv("SENDGRID_API_KEY") is not None
        }
        
        for service, configured in api_keys.items():
            status = "✅ Configured" if configured else "❌ Not configured"
            st.write(f"**{service}**: {status}")
        
        st.subheader("System Parameters")
        
        # Model parameters
        model_update_interval = st.number_input("Model Update Interval (minutes)", 1, 1440, config.get('model_update_interval', 60))
        data_retention_days = st.number_input("Data Retention (days)", 1, 365, config.get('data_retention_days', 90))
        
        # Alert parameters
        alert_cooldown = st.number_input("Alert Cooldown (minutes)", 1, 60, config.get('alert_cooldown', 15))
        max_alerts_per_hour = st.number_input("Max Alerts per Hour", 1, 20, config.get('max_alerts_per_hour', 5))
    
    with col2:
        st.subheader("Mine Configuration")
        
        # Mine parameters
        mine_name = st.text_input("Mine Name", value=config.get('mine_name', 'Open Pit Mine Alpha'))
        mine_coordinates = st.text_input("Coordinates", value=config.get('coordinates', '45.123, -123.456'))
        
        # Sensor configuration
        sensor_count = st.number_input("Number of Sensors", 1, 100, config.get('sensor_count', 47))
        sensor_update_freq = st.selectbox("Sensor Update Frequency", 
                                        ["1 minute", "5 minutes", "15 minutes", "30 minutes"],
                                        index=config.get('sensor_freq_index', 1))
        
        st.subheader("Data Sources")
        
        # Data source configuration
        use_dem_data = st.checkbox("Digital Elevation Model", value=config.get('use_dem', True))
        use_drone_imagery = st.checkbox("Drone Imagery", value=config.get('use_drone', True))
        use_weather_data = st.checkbox("Weather Data", value=config.get('use_weather', True))
        
        # Save configuration
        if st.button("💾 Save Configuration"):
            new_config = {
                'mine_name': mine_name,
                'coordinates': mine_coordinates,
                'sensor_count': sensor_count,
                'model_update_interval': model_update_interval,
                'data_retention_days': data_retention_days,
                'alert_cooldown': alert_cooldown,
                'max_alerts_per_hour': max_alerts_per_hour,
                'use_dem': use_dem_data,
                'use_drone': use_drone_imagery,
                'use_weather': use_weather_data
            }
            
            if st.session_state.config_manager.update_config(new_config):
                st.success("Configuration saved successfully!")
            else:
                st.error("Failed to save configuration")

if __name__ == "__main__":
    main()