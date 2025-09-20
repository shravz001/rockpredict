import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

class Visualizer:
    def __init__(self):
        self.color_schemes = {
            'risk_levels': {
                'low': '#2E8B57',      # Sea Green
                'medium': '#FFD700',   # Gold
                'high': '#FF8C00',     # Dark Orange
                'critical': '#DC143C'  # Crimson
            },
            'sensor_types': {
                'displacement': '#1f77b4',  # Blue
                'strain': '#ff7f0e',        # Orange
                'pore_pressure': '#2ca02c', # Green
                'vibration': '#d62728'      # Red
            }
        }
    
    def create_3d_mine_plot(self, mine_data):
        """Create 3D mine visualization with risk overlay"""
        terrain = mine_data['terrain']
        risk_overlay = mine_data['risk_overlay']
        sensors = mine_data['sensors']
        
        # Create 3D surface plot
        fig = go.Figure()
        
        # Add terrain surface
        fig.add_trace(go.Surface(
            x=terrain['X'],
            y=terrain['Y'],
            z=terrain['Z'],
            surfacecolor=risk_overlay,
            colorscale=[
                [0.0, self.color_schemes['risk_levels']['low']],
                [0.3, self.color_schemes['risk_levels']['medium']],
                [0.6, self.color_schemes['risk_levels']['high']],
                [1.0, self.color_schemes['risk_levels']['critical']]
            ],
            cmin=0,
            cmax=100,
            colorbar=dict(
                title="Risk Level (%)",
                titleside="right",
                tickmode="array",
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0%", "25%", "50%", "75%", "100%"],
                thickness=15,
                len=0.7
            ),
            showscale=True,
            name="Mine Terrain with Risk Overlay"
        ))
        
        # Add sensor locations
        if sensors:
            sensor_df = pd.DataFrame(sensors)
            
            # Group by sensor type for different colors
            for sensor_type in sensor_df['type'].unique():
                type_sensors = sensor_df[sensor_df['type'] == sensor_type]
                
                # Color based on status
                colors = []
                for status in type_sensors['status']:
                    if status == 'Online':
                        colors.append(self.color_schemes['sensor_types'][sensor_type])
                    elif status == 'Warning':
                        colors.append('#FFA500')  # Orange
                    else:
                        colors.append('#808080')  # Gray
                
                fig.add_trace(go.Scatter3d(
                    x=type_sensors['x'],
                    y=type_sensors['y'],
                    z=type_sensors['z'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=colors,
                        symbol='diamond' if sensor_type == 'displacement' else 
                               'square' if sensor_type == 'strain' else
                               'circle' if sensor_type == 'pore_pressure' else 'cross',
                        line=dict(width=2, color='white')
                    ),
                    text=[f"{sensor_type.title()}<br>ID: {id}<br>Status: {status}" 
                          for id, status in zip(type_sensors['id'], type_sensors['status'])],
                    hovertemplate="%{text}<br>Location: (%{x:.1f}, %{y:.1f}, %{z:.1f})<extra></extra>",
                    name=f"{sensor_type.title()} Sensors"
                ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': "3D Mine Visualization with Risk Assessment",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            scene=dict(
                xaxis_title="X Coordinate (m)",
                yaxis_title="Y Coordinate (m)",
                zaxis_title="Elevation (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2),
                    up=dict(x=0, y=0, z=1)
                ),
                aspectmode='manual',
                aspectratio=dict(x=1, y=0.6, z=0.4)
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            height=700,
            margin=dict(t=80, b=40, l=40, r=40)
        )
        
        return fig
    
    def create_risk_heatmap(self, risk_data, title="Risk Level Heatmap"):
        """Create 2D risk heatmap"""
        fig = go.Figure(data=go.Heatmap(
            z=risk_data['risk_levels'],
            x=risk_data['x_coords'],
            y=risk_data['y_coords'],
            colorscale=[
                [0.0, self.color_schemes['risk_levels']['low']],
                [0.3, self.color_schemes['risk_levels']['medium']],
                [0.6, self.color_schemes['risk_levels']['high']],
                [1.0, self.color_schemes['risk_levels']['critical']]
            ],
            zmin=0,
            zmax=100,
            colorbar=dict(
                title="Risk Level (%)",
                titleside="right"
            ),
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="X Coordinate (m)",
            yaxis_title="Y Coordinate (m)",
            height=500
        )
        
        return fig
    
    def create_sensor_network_plot(self, sensors_data):
        """Create sensor network visualization"""
        fig = go.Figure()
        
        # Create base mine outline
        mine_outline_x = [-500, 500, 500, -500, -500]
        mine_outline_y = [-300, -300, 300, 300, -300]
        
        fig.add_trace(go.Scatter(
            x=mine_outline_x,
            y=mine_outline_y,
            mode='lines',
            line=dict(color='black', width=3),
            name='Mine Boundary',
            showlegend=True
        ))
        
        # Add sensors by type
        for sensor_type in ['displacement', 'strain', 'pore_pressure', 'vibration']:
            type_sensors = [s for s in sensors_data if s['type'] == sensor_type]
            
            if type_sensors:
                x_coords = [s['x'] for s in type_sensors]
                y_coords = [s['y'] for s in type_sensors]
                statuses = [s['status'] for s in type_sensors]
                sensor_ids = [s['id'] for s in type_sensors]
                
                # Color based on status
                colors = []
                for status in statuses:
                    if status == 'Online':
                        colors.append(self.color_schemes['sensor_types'][sensor_type])
                    elif status == 'Warning':
                        colors.append('#FFA500')
                    else:
                        colors.append('#808080')
                
                fig.add_trace(go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=colors,
                        symbol='diamond' if sensor_type == 'displacement' else 
                               'square' if sensor_type == 'strain' else
                               'circle' if sensor_type == 'pore_pressure' else 'cross',
                        line=dict(width=2, color='white')
                    ),
                    text=[f"{sensor_type.title()}<br>ID: {id}<br>Status: {status}" 
                          for id, status in zip(sensor_ids, statuses)],
                    hovertemplate="%{text}<br>Location: (%{x:.1f}, %{y:.1f})<extra></extra>",
                    name=f"{sensor_type.title()} Sensors"
                ))
        
        # Add communication links (simulated)
        self._add_communication_links(fig, sensors_data)
        
        fig.update_layout(
            title="Sensor Network Layout",
            xaxis_title="X Coordinate (m)",
            yaxis_title="Y Coordinate (m)",
            height=600,
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    
    def _add_communication_links(self, fig, sensors_data):
        """Add communication links between sensors"""
        # Simulate mesh network connections
        online_sensors = [s for s in sensors_data if s['status'] == 'Online']
        
        for i, sensor in enumerate(online_sensors):
            # Connect to nearby sensors (simplified)
            for other_sensor in online_sensors[i+1:]:
                distance = np.sqrt((sensor['x'] - other_sensor['x'])**2 + 
                                 (sensor['y'] - other_sensor['y'])**2)
                
                # Only show connections within communication range
                if distance < 150:  # 150m range
                    fig.add_trace(go.Scatter(
                        x=[sensor['x'], other_sensor['x']],
                        y=[sensor['y'], other_sensor['y']],
                        mode='lines',
                        line=dict(color='lightblue', width=1, dash='dot'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    def create_temporal_risk_chart(self, risk_history):
        """Create temporal risk level chart"""
        fig = go.Figure()
        
        # Add risk level line
        fig.add_trace(go.Scatter(
            x=risk_history['timestamps'],
            y=risk_history['risk_levels'],
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=4),
            name='Risk Level',
            hovertemplate="Time: %{x}<br>Risk: %{y:.1f}%<extra></extra>"
        ))
        
        # Add risk threshold lines
        fig.add_hline(
            y=75, 
            line_dash="dash", 
            line_color="red", 
            annotation_text="Critical Threshold (75%)",
            annotation_position="bottom right"
        )
        
        fig.add_hline(
            y=50, 
            line_dash="dash", 
            line_color="orange", 
            annotation_text="High Risk Threshold (50%)",
            annotation_position="bottom right"
        )
        
        fig.add_hline(
            y=25, 
            line_dash="dash", 
            line_color="gold", 
            annotation_text="Medium Risk Threshold (25%)",
            annotation_position="bottom right"
        )
        
        # Color background based on risk levels
        fig.add_hrect(
            y0=0, y1=25, 
            fillcolor=self.color_schemes['risk_levels']['low'], 
            opacity=0.1, 
            layer="below", 
            line_width=0
        )
        fig.add_hrect(
            y0=25, y1=50, 
            fillcolor=self.color_schemes['risk_levels']['medium'], 
            opacity=0.1, 
            layer="below", 
            line_width=0
        )
        fig.add_hrect(
            y0=50, y1=75, 
            fillcolor=self.color_schemes['risk_levels']['high'], 
            opacity=0.1, 
            layer="below", 
            line_width=0
        )
        fig.add_hrect(
            y0=75, y1=100, 
            fillcolor=self.color_schemes['risk_levels']['critical'], 
            opacity=0.1, 
            layer="below", 
            line_width=0
        )
        
        fig.update_layout(
            title="Risk Level Over Time",
            xaxis_title="Time",
            yaxis_title="Risk Level (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_sensor_status_dashboard(self, sensor_data):
        """Create comprehensive sensor status dashboard"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Sensor Status Distribution', 'Signal Strength by Type', 
                          'Battery Levels', 'Reading Trends'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Status distribution pie chart
        status_counts = {}
        for sensor in sensor_data:
            status = sensor['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig.add_trace(
            go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.3,
                marker=dict(colors=['#2E8B57', '#FFD700', '#DC143C'])
            ),
            row=1, col=1
        )
        
        # 2. Signal strength by sensor type
        sensor_types = {}
        for sensor in sensor_data:
            sensor_type = sensor['type']
            if sensor_type not in sensor_types:
                sensor_types[sensor_type] = []
            # Simulate signal strength
            signal_strength = random.randint(60, 100) if sensor['status'] == 'Online' else 0
            sensor_types[sensor_type].append(signal_strength)
        
        for sensor_type, strengths in sensor_types.items():
            fig.add_trace(
                go.Bar(
                    x=[sensor_type],
                    y=[np.mean(strengths)],
                    name=f'{sensor_type.title()}',
                    marker_color=self.color_schemes['sensor_types'][sensor_type]
                ),
                row=1, col=2
            )
        
        # 3. Battery levels
        battery_ranges = {'0-25%': 0, '26-50%': 0, '51-75%': 0, '76-100%': 0}
        for sensor in sensor_data:
            battery = random.randint(20, 100) if sensor['status'] == 'Online' else 0
            if battery <= 25:
                battery_ranges['0-25%'] += 1
            elif battery <= 50:
                battery_ranges['26-50%'] += 1
            elif battery <= 75:
                battery_ranges['51-75%'] += 1
            else:
                battery_ranges['76-100%'] += 1
        
        fig.add_trace(
            go.Bar(
                x=list(battery_ranges.keys()),
                y=list(battery_ranges.values()),
                marker_color=['#DC143C', '#FF8C00', '#FFD700', '#2E8B57']
            ),
            row=2, col=1
        )
        
        # 4. Reading trends (simulated)
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        readings = [random.uniform(0.8, 1.2) for _ in timestamps]
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=readings,
                mode='lines+markers',
                name='Normalized Readings',
                line=dict(color='blue')
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="Comprehensive Sensor Status Dashboard",
            showlegend=False
        )
        
        return fig
    
    def create_geological_stability_map(self, stability_data):
        """Create geological stability visualization"""
        fig = go.Figure()
        
        # Add stability contours
        fig.add_trace(go.Contour(
            z=stability_data['stability_matrix'],
            x=stability_data['x_coords'],
            y=stability_data['y_coords'],
            colorscale=[
                [0, '#8B0000'],    # Dark red - Very unstable
                [0.25, '#FF4500'], # Orange red - Unstable
                [0.5, '#FFD700'],  # Gold - Moderate
                [0.75, '#ADFF2F'], # Green yellow - Stable
                [1, '#006400']     # Dark green - Very stable
            ],
            contours=dict(
                start=0,
                end=1,
                size=0.1,
            ),
            colorbar=dict(
                title="Stability Index",
                titleside="right"
            )
        ))
        
        # Add geological features
        if 'geological_features' in stability_data:
            for feature in stability_data['geological_features']:
                fig.add_trace(go.Scatter(
                    x=feature['x_coords'],
                    y=feature['y_coords'],
                    mode='lines',
                    line=dict(
                        color=feature['color'],
                        width=3,
                        dash='solid' if feature['type'] == 'fault' else 'dash'
                    ),
                    name=f"{feature['type'].title()}: {feature['name']}",
                    hovertemplate=f"{feature['type'].title()}: {feature['name']}<extra></extra>"
                ))
        
        fig.update_layout(
            title="Geological Stability Map",
            xaxis_title="X Coordinate (m)",
            yaxis_title="Y Coordinate (m)",
            height=600
        )
        
        return fig
    
    def create_alert_analytics_chart(self, alert_data):
        """Create alert analytics visualization"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Alert Frequency by Severity', 'Daily Alert Trends',
                          'Response Time Distribution', 'Location-based Alerts'),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "histogram"}, {"type": "bar"}]]
        )
        
        # 1. Alert frequency by severity
        severity_counts = alert_data.get('severity_counts', {})
        colors = [self.color_schemes['risk_levels'][sev.lower()] for sev in severity_counts.keys()]
        
        fig.add_trace(
            go.Bar(
                x=list(severity_counts.keys()),
                y=list(severity_counts.values()),
                marker_color=colors,
                name='Alert Count'
            ),
            row=1, col=1
        )
        
        # 2. Daily alert trends
        daily_data = alert_data.get('daily_trends', {})
        fig.add_trace(
            go.Scatter(
                x=list(daily_data.keys()),
                y=list(daily_data.values()),
                mode='lines+markers',
                name='Daily Alerts',
                line=dict(color='blue')
            ),
            row=1, col=2
        )
        
        # 3. Response time distribution
        response_times = alert_data.get('response_times', [])
        fig.add_trace(
            go.Histogram(
                x=response_times,
                nbinsx=20,
                name='Response Times',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # 4. Location-based alerts
        location_counts = alert_data.get('location_counts', {})
        fig.add_trace(
            go.Bar(
                y=list(location_counts.keys()),
                x=list(location_counts.values()),
                orientation='h',
                name='Alerts by Location',
                marker_color='orange'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="Alert Analytics Dashboard",
            showlegend=False
        )
        
        return fig
    
    def create_communication_status_chart(self, comm_data):
        """Create communication system status visualization"""
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('System Status', 'Message Volume', 'Success Rate'),
            specs=[[{"type": "indicator"}, {"type": "bar"}, {"type": "pie"}]]
        )
        
        # 1. Overall system health indicator
        overall_health = comm_data.get('overall_health', 85)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=overall_health,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "System Health (%)"},
                delta={'reference': 90},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ),
            row=1, col=1
        )
        
        # 2. Message volume by type
        message_volumes = comm_data.get('message_volumes', {})
        fig.add_trace(
            go.Bar(
                x=list(message_volumes.keys()),
                y=list(message_volumes.values()),
                name='Messages Sent',
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            ),
            row=1, col=2
        )
        
        # 3. Success rate
        success_data = comm_data.get('success_rates', {})
        fig.add_trace(
            go.Pie(
                labels=['Successful', 'Failed'],
                values=[success_data.get('successful', 90), success_data.get('failed', 10)],
                hole=0.3,
                marker=dict(colors=['#2E8B57', '#DC143C'])
            ),
            row=1, col=3
        )
        
        fig.update_layout(
            height=400,
            title_text="Communication System Status"
        )
        
        return fig
    
    def create_environmental_correlation_plot(self, env_data, risk_data):
        """Create environmental factors vs risk correlation plot"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Rainfall vs Risk', 'Temperature vs Risk',
                          'Humidity vs Risk', 'Wind Speed vs Risk')
        )
        
        # 1. Rainfall vs Risk
        fig.add_trace(
            go.Scatter(
                x=env_data.get('rainfall', []),
                y=risk_data.get('risk_levels', []),
                mode='markers',
                marker=dict(color='blue', opacity=0.6),
                name='Rainfall'
            ),
            row=1, col=1
        )
        
        # 2. Temperature vs Risk
        fig.add_trace(
            go.Scatter(
                x=env_data.get('temperature', []),
                y=risk_data.get('risk_levels', []),
                mode='markers',
                marker=dict(color='red', opacity=0.6),
                name='Temperature'
            ),
            row=1, col=2
        )
        
        # 3. Humidity vs Risk
        fig.add_trace(
            go.Scatter(
                x=env_data.get('humidity', []),
                y=risk_data.get('risk_levels', []),
                mode='markers',
                marker=dict(color='green', opacity=0.6),
                name='Humidity'
            ),
            row=2, col=1
        )
        
        # 4. Wind Speed vs Risk
        fig.add_trace(
            go.Scatter(
                x=env_data.get('wind_speed', []),
                y=risk_data.get('risk_levels', []),
                mode='markers',
                marker=dict(color='purple', opacity=0.6),
                name='Wind Speed'
            ),
            row=2, col=2
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Rainfall (mm)", row=1, col=1)
        fig.update_xaxes(title_text="Temperature (°C)", row=1, col=2)
        fig.update_xaxes(title_text="Humidity (%)", row=2, col=1)
        fig.update_xaxes(title_text="Wind Speed (km/h)", row=2, col=2)
        
        fig.update_yaxes(title_text="Risk Level (%)", row=1, col=1)
        fig.update_yaxes(title_text="Risk Level (%)", row=1, col=2)
        fig.update_yaxes(title_text="Risk Level (%)", row=2, col=1)
        fig.update_yaxes(title_text="Risk Level (%)", row=2, col=2)
        
        fig.update_layout(
            height=600,
            title_text="Environmental Factors vs Risk Level Correlation",
            showlegend=False
        )
        
        return fig
