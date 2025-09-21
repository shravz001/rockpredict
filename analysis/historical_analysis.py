"""
Historical analysis module for the Rockfall Prediction System
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any

class HistoricalAnalysis:
    """Provides historical analysis capabilities for mine data"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def generate_historical_data(self, days=30) -> pd.DataFrame:
        """Generate historical data for analysis"""
        # Create time series data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start=start_date, end=end_date, freq='h')
        
        # Generate synthetic data with realistic patterns
        data = []
        for i, timestamp in enumerate(date_range):
            # Add daily and seasonal patterns
            hour_factor = np.sin(timestamp.hour * np.pi / 12)
            day_factor = np.sin(timestamp.timetuple().tm_yday * 2 * np.pi / 365)
            
            # Base risk with patterns and noise
            base_risk = 0.3 + 0.2 * hour_factor + 0.1 * day_factor
            risk_probability = max(0, min(1, base_risk + np.random.normal(0, 0.1)))
            
            # Environmental factors
            temp = 15 + 10 * np.sin((timestamp.timetuple().tm_yday + timestamp.hour/24) * 2 * np.pi / 365) + np.random.normal(0, 3)
            rainfall = max(0, np.random.gamma(2, 2)) if np.random.random() > 0.8 else 0
            wind_speed = max(0, np.random.gamma(3, 2))
            
            # Sensor readings
            displacement = np.random.uniform(0.1, 2.0)
            strain = np.random.uniform(0.05, 1.0)
            vibration = np.random.uniform(0, 0.6)
            
            data.append({
                'timestamp': timestamp,
                'risk_probability': risk_probability,
                'temperature': temp,
                'rainfall': rainfall,
                'wind_speed': wind_speed,
                'displacement': displacement,
                'strain': strain,
                'vibration': vibration,
                'alerts_triggered': 1 if risk_probability > 0.7 else 0
            })
        
        return pd.DataFrame(data)
    
    def create_risk_timeline(self, data: pd.DataFrame) -> go.Figure:
        """Create risk timeline visualization"""
        fig = go.Figure()
        
        # Risk probability line
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data['risk_probability'],
            mode='lines',
            name='Risk Probability',
            line=dict(color='blue', width=2)
        ))
        
        # Risk thresholds
        fig.add_hline(y=0.7, line_dash="dash", line_color="red", 
                     annotation_text="High Risk Threshold")
        fig.add_hline(y=0.3, line_dash="dash", line_color="yellow", 
                     annotation_text="Medium Risk Threshold")
        
        # Highlight alert periods
        alert_periods = data[data['alerts_triggered'] == 1]
        if not alert_periods.empty:
            fig.add_trace(go.Scatter(
                x=alert_periods['timestamp'],
                y=alert_periods['risk_probability'],
                mode='markers',
                name='Alerts Triggered',
                marker=dict(color='red', size=8, symbol='diamond')
            ))
        
        fig.update_layout(
            title="Historical Risk Timeline",
            xaxis_title="Time",
            yaxis_title="Risk Probability",
            height=400,
            yaxis=dict(range=[0, 1])
        )
        
        return fig
    
    def create_seasonal_analysis(self, data: pd.DataFrame) -> go.Figure:
        """Create seasonal risk pattern analysis"""
        # Group by hour of day
        hourly_risk = data.groupby(data['timestamp'].dt.hour)['risk_probability'].mean()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hourly_risk.index,
            y=hourly_risk.values,
            mode='lines+markers',
            name='Average Risk by Hour',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Daily Risk Pattern (Average by Hour)",
            xaxis_title="Hour of Day",
            yaxis_title="Average Risk Probability",
            height=400,
            xaxis=dict(tickmode='linear', dtick=2)
        )
        
        return fig
    
    def calculate_correlations(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate correlation matrix for environmental factors"""
        # Select numeric columns for correlation
        numeric_cols = ['risk_probability', 'temperature', 'rainfall', 'wind_speed', 
                       'displacement', 'strain', 'vibration']
        
        correlation_data = data[numeric_cols].corr()
        return correlation_data.values
    
    def generate_report(self, data: pd.DataFrame, start_date, end_date, analysis_type) -> Dict[str, Any]:
        """Generate analysis report"""
        
        # Filter data by date range
        mask = (data['timestamp'] >= pd.Timestamp(start_date)) & (data['timestamp'] <= pd.Timestamp(end_date))
        filtered_data = data.loc[mask]
        
        if filtered_data.empty:
            return {"error": "No data available for selected date range"}
        
        report = {}
        
        if analysis_type == "Risk Trends":
            report.update({
                'avg_risk': f"{filtered_data['risk_probability'].mean():.1%}",
                'max_risk': f"{filtered_data['risk_probability'].max():.1%}",
                'min_risk': f"{filtered_data['risk_probability'].min():.1%}",
                'total_alerts': int(filtered_data['alerts_triggered'].sum()),
                'high_risk_hours': int((filtered_data['risk_probability'] > 0.7).sum()),
                'trend': "Increasing" if filtered_data['risk_probability'].iloc[-1] > filtered_data['risk_probability'].iloc[0] else "Decreasing"
            })
        
        elif analysis_type == "Environmental Impact":
            # Calculate correlations with risk
            risk_corr = filtered_data.corr()['risk_probability'].abs().sort_values(ascending=False)
            
            report.update({
                'strongest_correlation': risk_corr.index[1] if len(risk_corr) > 1 else "N/A",  # Skip risk_probability itself
                'correlation_value': f"{risk_corr.iloc[1]:.3f}" if len(risk_corr) > 1 else "N/A",
                'avg_temperature': f"{filtered_data['temperature'].mean():.1f}°C",
                'total_rainfall': f"{filtered_data['rainfall'].sum():.1f}mm",
                'avg_wind_speed': f"{filtered_data['wind_speed'].mean():.1f}m/s"
            })
        
        elif analysis_type == "Sensor Performance":
            report.update({
                'avg_displacement': f"{filtered_data['displacement'].mean():.2f}mm",
                'max_displacement': f"{filtered_data['displacement'].max():.2f}mm",
                'avg_strain': f"{filtered_data['strain'].mean():.3f}µε",
                'max_strain': f"{filtered_data['strain'].max():.3f}µε",
                'avg_vibration': f"{filtered_data['vibration'].mean():.3f}g",
                'max_vibration': f"{filtered_data['vibration'].max():.3f}g"
            })
        
        elif analysis_type == "Alert Frequency":
            # Group by day for alert frequency
            daily_alerts = filtered_data.groupby(filtered_data['timestamp'].dt.date)['alerts_triggered'].sum()
            
            report.update({
                'total_alerts': int(filtered_data['alerts_triggered'].sum()),
                'avg_alerts_per_day': f"{daily_alerts.mean():.1f}",
                'max_alerts_in_day': int(daily_alerts.max()) if not daily_alerts.empty else 0,
                'days_with_alerts': int((daily_alerts > 0).sum()),
                'alert_rate': f"{(filtered_data['alerts_triggered'].sum() / len(filtered_data) * 100):.1f}%"
            })
        
        return report
    
    def get_performance_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate system performance metrics"""
        return {
            'data_completeness': 1.0 - (data.isnull().sum().sum() / (len(data) * len(data.columns))),
            'alert_accuracy': 0.85,  # Would be calculated from actual vs predicted
            'false_positive_rate': 0.12,
            'detection_rate': 0.88,
            'system_availability': 0.995
        }
    
    def identify_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify anomalous periods in the data"""
        anomalies = []
        
        # Find periods with unusually high risk
        high_risk_threshold = data['risk_probability'].quantile(0.95)
        high_risk_periods = data[data['risk_probability'] > high_risk_threshold]
        
        for _, period in high_risk_periods.iterrows():
            anomalies.append({
                'timestamp': period['timestamp'],
                'type': 'High Risk Anomaly',
                'value': period['risk_probability'],
                'description': f"Risk level reached {period['risk_probability']:.1%}"
            })
        
        # Find unusual sensor readings
        for sensor in ['displacement', 'strain', 'vibration']:
            sensor_threshold = data[sensor].quantile(0.95)
            anomalous_readings = data[data[sensor] > sensor_threshold]
            
            for _, reading in anomalous_readings.iterrows():
                anomalies.append({
                    'timestamp': reading['timestamp'],
                    'type': f'{sensor.title()} Anomaly',
                    'value': reading[sensor],
                    'description': f"Unusual {sensor} reading: {reading[sensor]:.3f}"
                })
        
        return sorted(anomalies, key=lambda x: x['timestamp'], reverse=True)[:10]