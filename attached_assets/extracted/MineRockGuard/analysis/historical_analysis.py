import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from openai import OpenAI
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class HistoricalAnalysis:
    def __init__(self):
        self.analysis_cache = {}
        self.correlation_threshold = 0.3
        
        # Initialize OpenAI for advanced analysis
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_historical_data(self, days=90):
        """Generate comprehensive historical data for analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate daily data points
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        historical_records = []
        
        for date in date_range:
            # Simulate seasonal effects
            day_of_year = date.timetuple().tm_yday
            seasonal_factor = 0.3 * np.sin(2 * np.pi * day_of_year / 365)
            
            # Simulate weather patterns
            if day_of_year > 90 and day_of_year < 270:  # Spring/Summer
                temp_base = 20
                rainfall_prob = 0.3
            else:  # Fall/Winter
                temp_base = 5
                rainfall_prob = 0.6
            
            # Generate daily summary data
            daily_record = {
                'date': date,
                'day_of_year': day_of_year,
                'month': date.month,
                'season': self._get_season(date.month),
                'average_risk': max(0, min(1, 0.4 + seasonal_factor + np.random.normal(0, 0.15))),
                'max_risk': max(0, min(1, 0.6 + seasonal_factor + np.random.normal(0, 0.2))),
                'temperature': temp_base + np.random.normal(0, 8),
                'rainfall': max(0, np.random.exponential(5) if np.random.random() < rainfall_prob else 0),
                'wind_speed': max(0, np.random.gamma(2, 3)),
                'humidity': np.random.uniform(40, 90),
                'atmospheric_pressure': np.random.normal(1013, 15),
                'active_sensors': np.random.randint(42, 48),
                'alerts_triggered': np.random.poisson(2),
                'high_risk_zones': np.random.randint(0, 5),
                'critical_incidents': 1 if np.random.random() < 0.02 else 0,  # 2% chance per day
                'maintenance_events': 1 if np.random.random() < 0.1 else 0,   # 10% chance per day
                'equipment_downtime': np.random.exponential(0.5),  # hours
                'seismic_activity': np.random.gamma(1, 0.5),  # relative scale
                'ground_moisture': np.random.uniform(10, 60),  # percentage
                'slope_displacement': np.random.uniform(0, 3),  # mm/day
                'vibration_events': np.random.poisson(5),
                'weather_severity': self._calculate_weather_severity(temp_base, rainfall_prob)
            }
            
            # Add correlations between factors
            if daily_record['rainfall'] > 10:  # Heavy rain
                daily_record['average_risk'] = min(1, daily_record['average_risk'] * 1.3)
                daily_record['ground_moisture'] = min(100, daily_record['ground_moisture'] * 1.5)
                daily_record['slope_displacement'] *= 1.4
            
            if daily_record['temperature'] < 0:  # Freezing
                daily_record['average_risk'] = min(1, daily_record['average_risk'] * 1.2)
            
            if daily_record['seismic_activity'] > 2:  # High seismic activity
                daily_record['vibration_events'] *= 2
                daily_record['average_risk'] = min(1, daily_record['average_risk'] * 1.5)
            
            historical_records.append(daily_record)
        
        return pd.DataFrame(historical_records)
    
    def _get_season(self, month):
        """Determine season based on month"""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    def _calculate_weather_severity(self, temp_base, rainfall_prob):
        """Calculate weather severity index"""
        temp_severity = abs(temp_base - 15) / 20  # Optimal around 15°C
        rain_severity = rainfall_prob
        return min(1, (temp_severity + rain_severity) / 2)
    
    def create_risk_timeline(self, historical_data):
        """Create comprehensive risk timeline visualization"""
        fig = go.Figure()
        
        # Main risk trend line
        fig.add_trace(go.Scatter(
            x=historical_data['date'],
            y=historical_data['average_risk'],
            mode='lines',
            name='Average Daily Risk',
            line=dict(color='blue', width=2),
            hovertemplate='Date: %{x}<br>Risk: %{y:.2%}<extra></extra>'
        ))
        
        # Maximum risk trend
        fig.add_trace(go.Scatter(
            x=historical_data['date'],
            y=historical_data['max_risk'],
            mode='lines',
            name='Maximum Daily Risk',
            line=dict(color='red', width=1, dash='dash'),
            hovertemplate='Date: %{x}<br>Max Risk: %{y:.2%}<extra></extra>'
        ))
        
        # Critical incidents markers
        critical_dates = historical_data[historical_data['critical_incidents'] > 0]['date']
        critical_risks = historical_data[historical_data['critical_incidents'] > 0]['average_risk']
        
        if len(critical_dates) > 0:
            fig.add_trace(go.Scatter(
                x=critical_dates,
                y=critical_risks,
                mode='markers',
                name='Critical Incidents',
                marker=dict(color='red', size=12, symbol='triangle-up'),
                hovertemplate='Critical Incident<br>Date: %{x}<br>Risk Level: %{y:.2%}<extra></extra>'
            ))
        
        # Add moving average
        window = 7  # 7-day moving average
        if len(historical_data) >= window:
            moving_avg = historical_data['average_risk'].rolling(window=window).mean()
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=moving_avg,
                mode='lines',
                name=f'{window}-Day Moving Average',
                line=dict(color='green', width=2, dash='dot'),
                hovertemplate='Date: %{x}<br>Moving Avg: %{y:.2%}<extra></extra>'
            ))
        
        # Risk threshold lines
        fig.add_hline(y=0.85, line_dash="dash", line_color="red", 
                     annotation_text="Critical Threshold (85%)")
        fig.add_hline(y=0.7, line_dash="dash", line_color="orange", 
                     annotation_text="High Risk Threshold (70%)")
        fig.add_hline(y=0.3, line_dash="dash", line_color="yellow", 
                     annotation_text="Medium Risk Threshold (30%)")
        
        fig.update_layout(
            title="Historical Risk Analysis Timeline",
            xaxis_title="Date",
            yaxis_title="Risk Level",
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    def create_seasonal_analysis(self, historical_data):
        """Create seasonal pattern analysis"""
        # Group by season and calculate statistics
        seasonal_stats = historical_data.groupby('season').agg({
            'average_risk': ['mean', 'std', 'max'],
            'rainfall': ['mean', 'sum'],
            'temperature': ['mean', 'min', 'max'],
            'alerts_triggered': 'sum',
            'critical_incidents': 'sum'
        }).round(3)
        
        # Flatten column names
        seasonal_stats.columns = ['_'.join(col).strip() for col in seasonal_stats.columns]
        seasonal_stats.reset_index(inplace=True)
        
        # Create subplot figure
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Seasonal Risk Patterns', 'Temperature Variations', 
                          'Rainfall Patterns', 'Incident Frequency'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        seasons = seasonal_stats['season']
        
        # Risk patterns
        fig.add_trace(
            go.Bar(x=seasons, y=seasonal_stats['average_risk_mean'], 
                   name='Avg Risk', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Temperature variations
        fig.add_trace(
            go.Bar(x=seasons, y=seasonal_stats['temperature_mean'], 
                   name='Avg Temp', marker_color='orange'),
            row=1, col=2
        )
        
        # Rainfall patterns
        fig.add_trace(
            go.Bar(x=seasons, y=seasonal_stats['rainfall_sum'], 
                   name='Total Rainfall', marker_color='blue'),
            row=2, col=1
        )
        
        # Incident frequency
        fig.add_trace(
            go.Bar(x=seasons, y=seasonal_stats['critical_incidents_sum'], 
                   name='Critical Incidents', marker_color='red'),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Seasonal Analysis Dashboard",
            height=600,
            showlegend=False
        )
        
        return fig
    
    def calculate_correlations(self, historical_data):
        """Calculate correlation matrix for key variables"""
        # Select numerical columns for correlation analysis
        correlation_vars = [
            'average_risk', 'max_risk', 'temperature', 'rainfall', 
            'wind_speed', 'humidity', 'atmospheric_pressure', 
            'seismic_activity', 'ground_moisture', 'slope_displacement',
            'vibration_events', 'weather_severity'
        ]
        
        correlation_data = historical_data[correlation_vars].corr()
        
        return correlation_data
    
    def identify_risk_patterns(self, historical_data):
        """Identify patterns and anomalies in risk data"""
        patterns = {
            'trend_analysis': {},
            'cyclical_patterns': {},
            'anomalies': [],
            'risk_factors': {}
        }
        
        # Trend analysis
        risk_series = historical_data['average_risk'].values
        dates_numeric = np.arange(len(risk_series))
        
        # Linear trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(dates_numeric, risk_series)
        patterns['trend_analysis'] = {
            'slope': slope,
            'direction': 'increasing' if slope > 0 else 'decreasing',
            'strength': abs(r_value),
            'significance': p_value < 0.05
        }
        
        # Cyclical patterns (using FFT)
        from scipy.fft import fft, fftfreq
        
        fft_values = fft(risk_series - np.mean(risk_series))
        frequencies = fftfreq(len(risk_series))
        
        # Find dominant frequencies
        magnitude = np.abs(fft_values)
        dominant_freq_idx = np.argsort(magnitude)[-5:]  # Top 5 frequencies
        
        patterns['cyclical_patterns'] = {
            'dominant_periods': [1/abs(float(frequencies[i])) if frequencies[i] != 0 else float('inf') 
                               for i in dominant_freq_idx if frequencies[i] != 0],
            'strength': [float(magnitude[i]) for i in dominant_freq_idx]
        }
        
        # Anomaly detection using z-score
        z_scores = np.abs(stats.zscore(risk_series))
        anomaly_threshold = 2.5
        anomaly_indices = np.where(z_scores > anomaly_threshold)[0]
        
        patterns['anomalies'] = [
            {
                'date': historical_data.iloc[i]['date'].strftime('%Y-%m-%d'),
                'risk_level': risk_series[i],
                'z_score': z_scores[i],
                'context': self._analyze_anomaly_context(historical_data.iloc[i])
            }
            for i in anomaly_indices
        ]
        
        # Risk factor analysis
        risk_correlations = historical_data.corr()['average_risk'].abs().sort_values(ascending=False)
        patterns['risk_factors'] = {
            factor: correlation for factor, correlation in risk_correlations.items()
            if factor != 'average_risk' and abs(correlation) > self.correlation_threshold
        }
        
        return patterns
    
    def _analyze_anomaly_context(self, data_point):
        """Analyze context around anomalous risk levels"""
        context = []
        
        if data_point['rainfall'] > 15:
            context.append('Heavy rainfall')
        if data_point['temperature'] < 0:
            context.append('Freezing temperatures')
        if data_point['seismic_activity'] > 2:
            context.append('High seismic activity')
        if data_point['wind_speed'] > 20:
            context.append('Strong winds')
        if data_point['critical_incidents'] > 0:
            context.append('Critical incident occurred')
        
        return context if context else ['No obvious environmental factors']
    
    def generate_report(self, historical_data, start_date, end_date, analysis_type):
        """Generate comprehensive analysis report"""
        # Filter data by date range
        filtered_data = historical_data[
            (historical_data['date'] >= pd.to_datetime(start_date)) &
            (historical_data['date'] <= pd.to_datetime(end_date))
        ]
        
        report = {
            'analysis_period': f"{start_date} to {end_date}",
            'total_days': len(filtered_data),
            'analysis_type': analysis_type,
            'generated_at': datetime.now().isoformat()
        }
        
        if analysis_type == "Risk Trends":
            report.update(self._generate_risk_trends_report(filtered_data))
        elif analysis_type == "Sensor Performance":
            report.update(self._generate_sensor_performance_report(filtered_data))
        elif analysis_type == "Alert Frequency":
            report.update(self._generate_alert_frequency_report(filtered_data))
        elif analysis_type == "Environmental Impact":
            report.update(self._generate_environmental_impact_report(filtered_data))
        
        # Add AI analysis if available
        if self.openai_client:
            ai_insights = self._get_ai_insights(filtered_data, analysis_type)
            report['ai_insights'] = ai_insights
        
        return report
    
    def _generate_risk_trends_report(self, data):
        """Generate risk trends analysis report"""
        return {
            'average_risk_level': f"{data['average_risk'].mean():.1%}",
            'peak_risk_level': f"{data['max_risk'].max():.1%}",
            'high_risk_days': len(data[data['average_risk'] > 0.7]),
            'risk_volatility': f"{data['average_risk'].std():.3f}",
            'trend_direction': 'Increasing' if data['average_risk'].iloc[-1] > data['average_risk'].iloc[0] else 'Decreasing',
            'critical_incidents': data['critical_incidents'].sum(),
            'risk_trend_slope': np.polyfit(range(len(data)), data['average_risk'], 1)[0]
        }
    
    def _generate_sensor_performance_report(self, data):
        """Generate sensor performance report"""
        return {
            'average_active_sensors': f"{data['active_sensors'].mean():.0f}",
            'sensor_availability': f"{(data['active_sensors'].mean() / 47) * 100:.1f}%",
            'lowest_sensor_count': data['active_sensors'].min(),
            'maintenance_events': data['maintenance_events'].sum(),
            'equipment_downtime_hours': f"{data['equipment_downtime'].sum():.1f}",
            'sensor_reliability_score': f"{(1 - data['equipment_downtime'].mean() / 24) * 100:.1f}%"
        }
    
    def _generate_alert_frequency_report(self, data):
        """Generate alert frequency analysis report"""
        return {
            'total_alerts': data['alerts_triggered'].sum(),
            'average_daily_alerts': f"{data['alerts_triggered'].mean():.1f}",
            'peak_alert_day': data['alerts_triggered'].max(),
            'alert_free_days': len(data[data['alerts_triggered'] == 0]),
            'high_alert_days': len(data[data['alerts_triggered'] > 5]),
            'alert_efficiency_ratio': f"{(data['critical_incidents'].sum() / max(1, data['alerts_triggered'].sum())) * 100:.1f}%"
        }
    
    def _generate_environmental_impact_report(self, data):
        """Generate environmental impact analysis report"""
        rainfall_correlation = data['rainfall'].corr(data['average_risk'])
        temp_correlation = data['temperature'].corr(data['average_risk'])
        
        return {
            'rainfall_impact_correlation': f"{rainfall_correlation:.3f}",
            'temperature_impact_correlation': f"{temp_correlation:.3f}",
            'high_rainfall_days': len(data[data['rainfall'] > 10]),
            'extreme_weather_days': len(data[data['weather_severity'] > 0.7]),
            'weather_related_incidents': data[data['weather_severity'] > 0.5]['critical_incidents'].sum(),
            'seasonal_risk_variation': f"{data.groupby('season')['average_risk'].std().mean():.3f}"
        }
    
    def _get_ai_insights(self, data, analysis_type):
        """Get AI-powered insights using OpenAI"""
        try:
            # Prepare data summary for AI analysis
            data_summary = {
                'period': f"{len(data)} days",
                'avg_risk': float(data['average_risk'].mean()),
                'max_risk': float(data['max_risk'].max()),
                'critical_incidents': int(data['critical_incidents'].sum()),
                'environmental_factors': {
                    'avg_rainfall': float(data['rainfall'].mean()),
                    'avg_temperature': float(data['temperature'].mean()),
                    'seismic_activity': float(data['seismic_activity'].mean())
                },
                'correlations': {
                    'rainfall_risk': float(data['rainfall'].corr(data['average_risk'])),
                    'temperature_risk': float(data['temperature'].corr(data['average_risk'])),
                    'seismic_risk': float(data['seismic_activity'].corr(data['average_risk']))
                }
            }
            
            prompt = f"""
            Analyze the following mine safety data for {analysis_type} and provide insights:
            
            Data Summary: {json.dumps(data_summary, indent=2)}
            
            Please provide:
            1. Key findings and patterns
            2. Risk assessment insights
            3. Recommendations for improving safety
            4. Predictive insights for future monitoring
            
            Focus on actionable insights for mine operators. Respond in JSON format.
            """
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI analysis"}
            
        except Exception as e:
            return {"error": f"AI analysis unavailable: {str(e)}"}
    
    def create_predictive_model_performance(self, historical_data):
        """Analyze and visualize predictive model performance over time"""
        # Simulate model prediction accuracy over time
        dates = historical_data['date']
        
        # Simulate different model performance metrics
        accuracy_trend = 0.85 + 0.1 * np.sin(np.arange(len(dates)) * 2 * np.pi / 30) + np.random.normal(0, 0.02, len(dates))
        precision_trend = 0.82 + 0.08 * np.sin(np.arange(len(dates)) * 2 * np.pi / 45) + np.random.normal(0, 0.015, len(dates))
        recall_trend = 0.88 + 0.06 * np.sin(np.arange(len(dates)) * 2 * np.pi / 60) + np.random.normal(0, 0.02, len(dates))
        
        # Ensure values stay within realistic bounds
        accuracy_trend = np.clip(accuracy_trend, 0.7, 0.95)
        precision_trend = np.clip(precision_trend, 0.7, 0.95)
        recall_trend = np.clip(recall_trend, 0.75, 0.95)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates, y=accuracy_trend,
            mode='lines', name='Accuracy',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=precision_trend,
            mode='lines', name='Precision',
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=recall_trend,
            mode='lines', name='Recall',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Predictive Model Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Performance Metric",
            yaxis=dict(range=[0.6, 1.0], tickformat='.0%'),
            hovermode='x unified'
        )
        
        return fig
    
    def analyze_maintenance_effectiveness(self, historical_data):
        """Analyze the effectiveness of maintenance activities"""
        # Find periods before and after maintenance events
        maintenance_days = historical_data[historical_data['maintenance_events'] > 0]
        
        effectiveness_analysis = []
        
        for _, maintenance_day in maintenance_days.iterrows():
            maintenance_date = maintenance_day['date']
            
            # Get 7 days before and after maintenance
            before_period = historical_data[
                (historical_data['date'] >= maintenance_date - timedelta(days=7)) &
                (historical_data['date'] < maintenance_date)
            ]
            
            after_period = historical_data[
                (historical_data['date'] > maintenance_date) &
                (historical_data['date'] <= maintenance_date + timedelta(days=7))
            ]
            
            if len(before_period) > 0 and len(after_period) > 0:
                risk_before = before_period['average_risk'].mean()
                risk_after = after_period['average_risk'].mean()
                risk_reduction = risk_before - risk_after
                
                effectiveness_analysis.append({
                    'maintenance_date': maintenance_date,
                    'risk_before': risk_before,
                    'risk_after': risk_after,
                    'risk_reduction': risk_reduction,
                    'effectiveness_score': max(0, risk_reduction / risk_before) if risk_before > 0 else 0
                })
        
        if effectiveness_analysis:
            avg_effectiveness = np.mean([a['effectiveness_score'] for a in effectiveness_analysis])
            total_risk_reduction = sum([a['risk_reduction'] for a in effectiveness_analysis])
            
            return {
                'maintenance_events_analyzed': len(effectiveness_analysis),
                'average_effectiveness_score': f"{avg_effectiveness:.1%}",
                'total_risk_reduction': f"{total_risk_reduction:.3f}",
                'most_effective_date': max(effectiveness_analysis, key=lambda x: x['effectiveness_score'])['maintenance_date'].strftime('%Y-%m-%d'),
                'recommendations': self._generate_maintenance_recommendations(effectiveness_analysis)
            }
        else:
            return {
                'maintenance_events_analyzed': 0,
                'message': 'Insufficient data for maintenance effectiveness analysis'
            }
    
    def _generate_maintenance_recommendations(self, effectiveness_data):
        """Generate maintenance recommendations based on effectiveness analysis"""
        recommendations = []
        
        avg_effectiveness = np.mean([a['effectiveness_score'] for a in effectiveness_data])
        
        if avg_effectiveness < 0.3:
            recommendations.append("Maintenance procedures may need review - low effectiveness detected")
        
        if avg_effectiveness > 0.7:
            recommendations.append("Current maintenance approach is highly effective - continue current practices")
        
        # Find seasonal patterns in maintenance effectiveness
        seasonal_effectiveness = {}
        for analysis in effectiveness_data:
            month = analysis['maintenance_date'].month
            season = self._get_season(month)
            if season not in seasonal_effectiveness:
                seasonal_effectiveness[season] = []
            seasonal_effectiveness[season].append(analysis['effectiveness_score'])
        
        if seasonal_effectiveness:
            best_season = max(seasonal_effectiveness.keys(), 
                            key=lambda s: np.mean(seasonal_effectiveness[s]))
            recommendations.append(f"Maintenance appears most effective during {best_season}")
        
        return recommendations

