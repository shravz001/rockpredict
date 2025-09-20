import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class RealTimeDashboard:
    def __init__(self):
        self.color_scheme = {
            'low': '#00FF00',      # Green
            'medium': '#FFFF00',   # Yellow  
            'high': '#FF8000',     # Orange
            'critical': '#FF0000'  # Red
        }
        
    def create_risk_heatmap(self, data):
        """Create risk heatmap for the mine site"""
        sensors = data['sensors']
        
        # Extract coordinates and risk levels
        lats = []
        lons = []
        risks = []
        sensor_ids = []
        zones = []
        
        for sensor in sensors:
            if sensor['status'] == 'online':
                coords = sensor['coordinates']
                lats.append(coords['lat'])
                lons.append(coords['lon'])
                risks.append(sensor['risk_probability'])
                sensor_ids.append(sensor['id'])
                zones.append(sensor['zone'])
        
        # Create the heatmap
        fig = go.Figure()
        
        # Add scatter plot for sensors
        fig.add_trace(go.Scatter(
            x=lons,
            y=lats,
            mode='markers',
            marker=dict(
                size=[max(10, r * 30) for r in risks],  # Size based on risk
                color=risks,
                colorscale='RdYlGn_r',  # Reverse Red-Yellow-Green
                showscale=True,
                colorbar=dict(
                    title=dict(text="Risk Level", side="right"),
                    tickmode="array",
                    tickvals=[0, 0.3, 0.7, 0.85, 1.0],
                    ticktext=["0%", "30%", "70%", "85%", "100%"]
                ),
                cmin=0,
                cmax=1,
                opacity=0.8
            ),
            text=[f"Sensor: {sid}<br>Zone: {zone}<br>Risk: {risk:.1%}" 
                  for sid, zone, risk in zip(sensor_ids, zones, risks)],
            hovertemplate='%{text}<br>Coordinates: (%{x:.6f}, %{y:.6f})<extra></extra>',
            name='Sensors'
        ))
        
        # Add zone boundaries (simplified representation)
        zone_centers = self._calculate_zone_centers(sensors)
        for zone_name, center in zone_centers.items():
            if center['risk'] > 0.3:  # Only show zones with elevated risk
                # Create circular zone boundary
                theta = np.linspace(0, 2*np.pi, 20)
                radius = 0.002  # Degrees (roughly 200m)
                zone_lats = center['lat'] + radius * np.cos(theta)
                zone_lons = center['lon'] + radius * np.sin(theta)
                
                # Determine zone color based on risk
                zone_color = self._get_risk_color(center['risk'])
                
                fig.add_trace(go.Scatter(
                    x=zone_lons,
                    y=zone_lats,
                    mode='lines',
                    line=dict(color=zone_color, width=3, dash='dash'),
                    fill='toself',
                    fillcolor=zone_color,
                    opacity=0.2,
                    name=f"{zone_name} Boundary",
                    showlegend=False,
                    hovertemplate=f"{zone_name}<br>Average Risk: {center['risk']:.1%}<extra></extra>"
                ))
        
        # Update layout
        fig.update_layout(
            title="Real-Time Mine Risk Heatmap",
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            hovermode='closest',
            width=800,
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        # Add risk level annotations
        self._add_risk_annotations(fig)
        
        return fig
    
    def _calculate_zone_centers(self, sensors):
        """Calculate center coordinates and average risk for each zone"""
        zone_data = {}
        
        for sensor in sensors:
            zone = sensor['zone']
            if zone not in zone_data:
                zone_data[zone] = {
                    'lats': [],
                    'lons': [],
                    'risks': []
                }
            
            coords = sensor['coordinates']
            zone_data[zone]['lats'].append(coords['lat'])
            zone_data[zone]['lons'].append(coords['lon'])
            zone_data[zone]['risks'].append(sensor['risk_probability'])
        
        zone_centers = {}
        for zone, data in zone_data.items():
            zone_centers[zone] = {
                'lat': np.mean(data['lats']),
                'lon': np.mean(data['lons']),
                'risk': np.mean(data['risks']),
                'sensor_count': len(data['lats'])
            }
        
        return zone_centers
    
    def _get_risk_color(self, risk_level):
        """Get color based on risk level"""
        if risk_level >= 0.85:
            return self.color_scheme['critical']
        elif risk_level >= 0.7:
            return self.color_scheme['high']
        elif risk_level >= 0.3:
            return self.color_scheme['medium']
        else:
            return self.color_scheme['low']
    
    def _add_risk_annotations(self, fig):
        """Add risk level annotations to the figure"""
        # Add legend as annotations
        annotations = [
            dict(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text="<b>Risk Levels:</b>",
                showarrow=False,
                font=dict(size=12, color="black"),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1
            ),
            dict(
                x=0.02, y=0.93,
                xref='paper', yref='paper',
                text="🟢 Low (0-30%)",
                showarrow=False,
                font=dict(size=10, color="green")
            ),
            dict(
                x=0.02, y=0.89,
                xref='paper', yref='paper',
                text="🟡 Medium (30-70%)",
                showarrow=False,
                font=dict(size=10, color="orange")
            ),
            dict(
                x=0.02, y=0.85,
                xref='paper', yref='paper',
                text="🟠 High (70-85%)",
                showarrow=False,
                font=dict(size=10, color="darkorange")
            ),
            dict(
                x=0.02, y=0.81,
                xref='paper', yref='paper',
                text="🔴 Critical (85-100%)",
                showarrow=False,
                font=dict(size=10, color="red")
            )
        ]
        
        fig.update_layout(annotations=annotations)
    
    def get_active_alerts(self, data):
        """Get list of active alerts based on current data"""
        alerts = []
        sensors = data['sensors']
        
        for sensor in sensors:
            risk = sensor['risk_probability']
            
            if risk >= 0.85:
                alerts.append({
                    'severity': 'critical',
                    'message': f'Critical risk detected - immediate evacuation recommended',
                    'zone': sensor['zone'],
                    'sensor_id': sensor['id'],
                    'risk_level': risk,
                    'timestamp': datetime.now()
                })
            elif risk >= 0.7:
                alerts.append({
                    'severity': 'high',
                    'message': f'High risk detected - restrict access and increase monitoring',
                    'zone': sensor['zone'],
                    'sensor_id': sensor['id'],
                    'risk_level': risk,
                    'timestamp': datetime.now()
                })
            elif risk >= 0.5:  # Medium-high threshold for alerts
                alerts.append({
                    'severity': 'medium',
                    'message': f'Elevated risk detected - monitor closely',
                    'zone': sensor['zone'],
                    'sensor_id': sensor['id'],
                    'risk_level': risk,
                    'timestamp': datetime.now()
                })
        
        # Sort by severity and risk level
        severity_order = {'critical': 0, 'high': 1, 'medium': 2}
        alerts.sort(key=lambda x: (severity_order[x['severity']], -x['risk_level']))
        
        return alerts
    
    def create_sensor_status_chart(self, data):
        """Create chart showing sensor status distribution"""
        sensors = data['sensors']
        
        # Count sensors by status
        online_count = sum(1 for s in sensors if s['status'] == 'online')
        offline_count = len(sensors) - online_count
        
        # Count by risk level
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for sensor in sensors:
            if sensor['status'] == 'online':
                risk = sensor['risk_probability']
                if risk >= 0.85:
                    risk_counts['critical'] += 1
                elif risk >= 0.7:
                    risk_counts['high'] += 1
                elif risk >= 0.3:
                    risk_counts['medium'] += 1
                else:
                    risk_counts['low'] += 1
        
        # Create pie chart for sensor status
        fig_status = go.Figure(data=[go.Pie(
            labels=['Online', 'Offline'],
            values=[online_count, offline_count],
            marker_colors=['green', 'red'],
            hole=0.4
        )])
        
        fig_status.update_layout(
            title="Sensor Network Status",
            annotations=[dict(text=f'{online_count}/{len(sensors)}', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        # Create bar chart for risk distribution
        fig_risk = go.Figure(data=[go.Bar(
            x=list(risk_counts.keys()),
            y=list(risk_counts.values()),
            marker_color=[self.color_scheme[level] for level in risk_counts.keys()]
        )])
        
        fig_risk.update_layout(
            title="Risk Level Distribution",
            xaxis_title="Risk Level",
            yaxis_title="Number of Sensors"
        )
        
        return fig_status, fig_risk
    
    def create_environmental_dashboard(self, data):
        """Create environmental conditions dashboard"""
        env = data['environmental']
        
        # Create gauge charts for key environmental factors
        fig = go.Figure()
        
        # Temperature gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=env['temperature'],
            domain={'x': [0, 0.33], 'y': [0.5, 1]},
            title={'text': "Temperature (°C)"},
            delta={'reference': 15},
            gauge={
                'axis': {'range': [None, 40]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 10], 'color': "lightblue"},
                    {'range': [10, 25], 'color': "lightgreen"},
                    {'range': [25, 40], 'color': "lightyellow"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 35
                }
            }
        ))
        
        # Rainfall gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=env['rainfall'],
            domain={'x': [0.33, 0.66], 'y': [0.5, 1]},
            title={'text': "Rainfall (mm/h)"},
            gauge={
                'axis': {'range': [None, 20]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2], 'color': "lightgreen"},
                    {'range': [2, 10], 'color': "lightyellow"},
                    {'range': [10, 20], 'color': "lightcoral"}
                ]
            }
        ))
        
        # Wind speed gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=env['wind_speed'],
            domain={'x': [0.66, 1], 'y': [0.5, 1]},
            title={'text': "Wind Speed (m/s)"},
            gauge={
                'axis': {'range': [None, 30]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgreen"},
                    {'range': [5, 15], 'color': "lightyellow"},
                    {'range': [15, 30], 'color': "lightcoral"}
                ]
            }
        ))
        
        # Humidity and pressure indicators
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=env['humidity'],
            domain={'x': [0, 0.5], 'y': [0, 0.4]},
            title={'text': "Humidity (%)"},
            delta={'reference': 60}
        ))
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=env['atmospheric_pressure'],
            domain={'x': [0.5, 1], 'y': [0, 0.4]},
            title={'text': "Pressure (hPa)"},
            delta={'reference': 1013}
        ))
        
        fig.update_layout(
            title="Environmental Conditions",
            height=600
        )
        
        return fig
    
    def create_system_health_dashboard(self, lorawan_status, radio_status):
        """Create system health monitoring dashboard"""
        # Communication systems health
        fig = go.Figure()
        
        # LoRaWAN status
        lorawan_health = lorawan_status['coverage'] * 100
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=lorawan_health,
            domain={'x': [0, 0.5], 'y': [0.5, 1]},
            title={'text': "LoRaWAN Network"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightcoral"},
                    {'range': [50, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        # Radio backup health
        radio_health = (1 - radio_status['error_rate']) * 100
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=radio_health,
            domain={'x': [0.5, 1], 'y': [0.5, 1]},
            title={'text': "Radio Backup"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightcoral"},
                    {'range': [50, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ]
            }
        ))
        
        # System uptime
        uptime = np.random.uniform(95, 99.9)  # Simulate system uptime
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=uptime,
            domain={'x': [0, 0.5], 'y': [0, 0.4]},
            title={'text': "System Uptime (%)"},
            delta={'reference': 99, 'increasing': {'color': "green"}}
        ))
        
        # Active sensors percentage
        active_sensors = (lorawan_status['devices'] / lorawan_status['total_devices']) * 100
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=active_sensors,
            domain={'x': [0.5, 1], 'y': [0, 0.4]},
            title={'text': "Active Sensors (%)"},
            delta={'reference': 95, 'increasing': {'color': "green"}}
        ))
        
        fig.update_layout(
            title="System Health Dashboard",
            height=600
        )
        
        return fig
