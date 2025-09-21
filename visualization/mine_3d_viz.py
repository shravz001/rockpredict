import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
import time

class Mine3DVisualizer:
    def __init__(self):
        self.color_schemes = {
            'Risk-based': {
                'low': '#00FF00',      # Green
                'medium': '#FFFF00',   # Yellow
                'high': '#FF8000',     # Orange
                'critical': '#FF0000'  # Red
            },
            'Elevation': px.colors.sequential.Viridis,
            'Geological': {
                'limestone': '#E6E6FA',
                'sandstone': '#F4A460',
                'shale': '#708090',
                'granite': '#696969'
            }
        }
        self.blink_state = 0  # For blinking animation
    
    def create_3d_mine_view(self, mine_data):
        """Create comprehensive 3D visualization of the mine"""
        fig = go.Figure()
        
        # Add terrain surface
        dem_data = mine_data['dem']
        x_terrain = np.array(dem_data['x'])
        y_terrain = np.array(dem_data['y'])
        z_terrain = np.array(dem_data['z'])
        
        # Create surface plot for terrain
        fig.add_trace(go.Surface(
            x=x_terrain,
            y=y_terrain,
            z=z_terrain,
            colorscale='Earth',
            opacity=0.7,
            name='Terrain',
            showscale=False,
            hovertemplate='X: %{x}<br>Y: %{y}<br>Elevation: %{z}m<extra></extra>'
        ))
        
        # Add risk zones as colored overlays
        zones = mine_data['zones']
        for zone in zones:
            self._add_risk_zone(fig, zone)
        
        # Add sensor network
        sensors = mine_data['sensor_network']
        self._add_sensor_network(fig, sensors)
        
        # Add mine infrastructure
        self._add_mine_infrastructure(fig, mine_data)
        
        # Configure enhanced layout for clarity
        fig.update_layout(
            title={
                'text': "<b>3D Mine Risk Assessment</b><br><span style='font-size:14px'>⚠️ High risk zones blink | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low</span>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            scene=dict(
                xaxis_title="X Coordinate (m)",
                yaxis_title="Y Coordinate (m)",
                zaxis_title="Elevation (m)",
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.5)  # Better viewing angle
                ),
                aspectmode='cube',  # Better proportions
                bgcolor='rgba(240,240,240,0.1)',  # Light background
                xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
                yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
                zaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1)
            ),
            width=1100,
            height=800,
            margin=dict(l=50, r=200, t=100, b=50),
            legend=dict(
                x=1.02,
                y=1,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='gray',
                borderwidth=1,
                font=dict(size=12)
            ),
            showlegend=True
        )
        
        return fig
    
    def _add_risk_zone(self, fig, zone):
        """Add prominent risk zone visualization with blinking for high-risk areas"""
        center = zone['center_coordinates']
        risk_level = zone['risk_level']
        
        # Enhanced color and visibility based on risk level
        if risk_level >= 0.7:  # Critical/High risk - RED with blinking
            color = '#FF0000'  # Bright red
            fill_color = 'rgba(255, 0, 0, 0.4)'
            border_width = 12
            marker_size = 20
            blink_effect = True
        elif risk_level >= 0.5:  # Medium-High risk - ORANGE
            color = '#FF6600'
            fill_color = 'rgba(255, 102, 0, 0.3)'
            border_width = 8
            marker_size = 16
            blink_effect = False
        elif risk_level >= 0.3:  # Medium risk - YELLOW
            color = '#FFAA00'
            fill_color = 'rgba(255, 170, 0, 0.25)'
            border_width = 6
            marker_size = 12
            blink_effect = False
        else:  # Low risk - GREEN
            color = '#00AA00'
            fill_color = 'rgba(0, 170, 0, 0.2)'
            border_width = 4
            marker_size = 10
            blink_effect = False
        
        # Create larger, more visible risk zone
        radius = 100  # Larger radius for better visibility
        theta = np.linspace(0, 2*np.pi, 30)  # More points for smoother circle
        
        # Zone boundary at terrain level
        zone_x = center['x'] + radius * np.cos(theta)
        zone_y = center['y'] + radius * np.sin(theta)
        zone_z = np.full_like(zone_x, center['z'] + 2)  # Just above terrain
        
        # Create filled surface for risk zone
        # Create a mesh grid for the filled area
        r_fill = np.linspace(0, radius, 10)
        theta_fill = np.linspace(0, 2*np.pi, 30)
        R, THETA = np.meshgrid(r_fill, theta_fill)
        X_fill = center['x'] + R * np.cos(THETA)
        Y_fill = center['y'] + R * np.sin(THETA)
        Z_fill = np.full_like(X_fill, center['z'] + 1)
        
        # Add filled surface for the risk zone
        fig.add_trace(go.Surface(
            x=X_fill,
            y=Y_fill,
            z=Z_fill,
            colorscale=[[0, fill_color], [1, fill_color]],
            showscale=False,
            opacity=0.6 if blink_effect else 0.4,
            name=f"🔴 Critical Risk Zones" if risk_level >= 0.7 else f"🟠 High Risk Zones" if risk_level >= 0.5 else f"🟡 Medium Risk Zones" if risk_level >= 0.3 else f"🟢 Low Risk Zones",
            legendgroup=f"risk_zones",
            showlegend=risk_level >= 0.7,  # Only show high-risk zones in legend
            hovertemplate=f"<b>{zone['name']}</b><br>Risk Level: {risk_level:.1%}<br>Status: {'⚠️ HIGH RISK' if risk_level >= 0.7 else '⚡ MEDIUM RISK' if risk_level >= 0.3 else '✅ LOW RISK'}<extra></extra>"
        ))
        
        # Add prominent zone boundary
        fig.add_trace(go.Scatter3d(
            x=zone_x,
            y=zone_y,
            z=zone_z,
            mode='lines',
            line=dict(
                color=color,
                width=border_width
            ),
            name=f"{zone['name']} Boundary",
            showlegend=False,
            hovertemplate=f"Zone: {zone['name']}<br>Risk: {risk_level:.1%}<extra></extra>"
        ))
        
        # Add large, prominent center marker
        marker_symbol = 'diamond' if risk_level >= 0.7 else 'circle'
        fig.add_trace(go.Scatter3d(
            x=[center['x']],
            y=[center['y']],
            z=[center['z'] + 15],
            mode='markers+text',
            marker=dict(
                size=marker_size,
                color=color,
                symbol=marker_symbol,
                line=dict(width=3, color='white'),
                opacity=1.0
            ),
            text=[f"⚠️ {zone['name']}" if risk_level >= 0.7 else zone['name']],
            textposition='top center',
            textfont=dict(size=14, color=color),
            name=f"{zone['name']} Center",
            showlegend=False,
            hovertemplate=f"<b>Zone: {zone['name']}</b><br>Risk Level: {risk_level:.1%}<br>Coordinates: ({center['x']:.0f}, {center['y']:.0f})<br>Type: {zone.get('geological_type', 'Unknown')}<extra></extra>"
        ))
        
        # Add blinking effect for high-risk zones by adding a secondary marker
        if blink_effect:
            # Calculate blinking opacity based on current time
            current_time = time.time()
            blink_cycle = (current_time * 2) % 2  # 2-second cycle
            blink_opacity = 0.3 + 0.7 * abs(np.sin(blink_cycle * np.pi))  # Smooth blinking
            
            fig.add_trace(go.Scatter3d(
                x=[center['x']],
                y=[center['y']],
                z=[center['z'] + 20],
                mode='markers',
                marker=dict(
                    size=25,
                    color='red',
                    symbol='circle',
                    line=dict(width=4, color='yellow'),
                    opacity=blink_opacity
                ),
                name=f"🚨 {zone['name']} ALERT",
                showlegend=True,
                hovertemplate=f"<b>🚨 HIGH RISK ALERT</b><br>Zone: {zone['name']}<br>Risk: {risk_level:.1%}<br>Immediate attention required!<extra></extra>"
            ))
            
            # Add pulsing border effect
            fig.add_trace(go.Scatter3d(
                x=zone_x,
                y=zone_y,
                z=zone_z + 3,
                mode='lines',
                line=dict(
                    color='red',
                    width=border_width + 4,
                    dash='dash'
                ),
                opacity=0.7 + 0.3 * abs(np.sin(blink_cycle * np.pi * 1.5)),  # Faster pulse
                name=f"⚠️ {zone['name']} Warning Border",
                showlegend=False,
                hovertemplate=f"High-Risk Zone Border: {zone['name']}<extra></extra>"
            ))
    
    def _add_sensor_network(self, fig, sensors):
        """Add simplified, cleaner sensor network visualization"""
        # Simplify sensor visualization - show only active sensors and group by status
        active_sensors = [s for s in sensors if s.get('status') == 'online']
        warning_sensors = [s for s in sensors if s.get('risk_probability', 0) > 0.7]
        
        # Show only active sensors with clean markers
        if active_sensors:
            x_coords = [s['coordinates']['x'] for s in active_sensors]
            y_coords = [s['coordinates']['y'] for s in active_sensors]
            z_coords = [s['coordinates']['z'] for s in active_sensors]
            sensor_ids = [s['id'] for s in active_sensors]
            risk_levels = [s.get('risk_probability', 0) for s in active_sensors]
            
            # Color sensors by risk level instead of type for clarity
            colors = ['red' if risk >= 0.7 else 'orange' if risk >= 0.5 else 'green' for risk in risk_levels]
            
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    size=6,
                    color=colors,
                    symbol='circle',
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                name="Active Sensors",
                text=sensor_ids,
                hovertemplate="<b>Sensor: %{text}</b><br>Risk Level: %{customdata:.1%}<br>Status: Online<extra></extra>",
                customdata=risk_levels
            ))
        
        # Highlight high-risk sensors with larger markers
        if warning_sensors:
            x_warning = [s['coordinates']['x'] for s in warning_sensors]
            y_warning = [s['coordinates']['y'] for s in warning_sensors]
            z_warning = [s['coordinates']['z'] + 5 for s in warning_sensors]  # Slightly elevated
            warning_ids = [s['id'] for s in warning_sensors]
            warning_risks = [s.get('risk_probability', 0) for s in warning_sensors]
            
            fig.add_trace(go.Scatter3d(
                x=x_warning,
                y=y_warning,
                z=z_warning,
                mode='markers',
                marker=dict(
                    size=12,
                    color='red',
                    symbol='diamond',
                    opacity=0.9,
                    line=dict(width=2, color='yellow')
                ),
                name="⚠️ High-Risk Sensors",
                text=[f"⚠️ {id}" for id in warning_ids],
                hovertemplate="<b>⚠️ HIGH RISK SENSOR</b><br>ID: %{text}<br>Risk Level: %{customdata:.1%}<br>Requires immediate attention!<extra></extra>",
                customdata=warning_risks
            ))
    
    def _add_mine_infrastructure(self, fig, mine_data):
        """Add mine infrastructure elements"""
        # Add access roads (simplified)
        road_points = [
            {'start': (100, 100, 1250), 'end': (500, 400, 1200)},
            {'start': (500, 400, 1200), 'end': (800, 600, 1230)},
            {'start': (300, 200, 1240), 'end': (600, 500, 1210)},
        ]
        
        for i, road in enumerate(road_points):
            start, end = road['start'], road['end']
            fig.add_trace(go.Scatter3d(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                z=[start[2], end[2]],
                mode='lines',
                line=dict(color='black', width=6),
                name=f"Access Road {i+1}" if i == 0 else "",
                showlegend=i == 0,
                hovertemplate="Access Road<extra></extra>"
            ))
        
        # Add equipment zones
        equipment_zones = [
            {'name': 'Crusher', 'pos': (200, 150, 1280), 'color': 'brown'},
            {'name': 'Processing Plant', 'pos': (750, 650, 1290), 'color': 'gray'},
            {'name': 'Maintenance', 'pos': (600, 200, 1270), 'color': 'orange'},
        ]
        
        for equipment in equipment_zones:
            pos = equipment['pos']
            fig.add_trace(go.Scatter3d(
                x=[pos[0]],
                y=[pos[1]],
                z=[pos[2]],
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=equipment['color'],
                    symbol='square',
                    opacity=0.8
                ),
                text=[equipment['name']],
                textposition='top center',
                name=equipment['name'],
                hovertemplate=f"{equipment['name']}<br>Location: ({pos[0]}, {pos[1]}, {pos[2]})<extra></extra>"
            ))
    
    def update_3d_view(self, mine_data, view_mode, show_sensors, show_risk_zones, color_scheme):
        """Update 3D visualization based on user preferences"""
        fig = go.Figure()
        
        # Base terrain - always shown
        dem_data = mine_data['dem']
        x_terrain = np.array(dem_data['x'])
        y_terrain = np.array(dem_data['y'])
        z_terrain = np.array(dem_data['z'])
        
        # Apply color scheme
        if color_scheme == 'Elevation':
            colorscale = 'Viridis'
        elif color_scheme == 'Geological':
            colorscale = 'Earth'
        else:  # Risk-based
            colorscale = 'RdYlGn_r'
        
        fig.add_trace(go.Surface(
            x=x_terrain,
            y=y_terrain,
            z=z_terrain,
            colorscale=colorscale,
            opacity=0.7,
            name='Terrain',
            showscale=False
        ))
        
        # Add elements based on view mode
        if view_mode == "Risk Overlay" and show_risk_zones:
            zones = mine_data['zones']
            for zone in zones:
                self._add_risk_zone(fig, zone)
        
        if view_mode == "Sensor Network" and show_sensors:
            sensors = mine_data['sensor_network']
            self._add_sensor_network(fig, sensors)
        
        if view_mode == "Geological Layers":
            self._add_geological_layers(fig, mine_data)
        
        # Standard layout
        fig.update_layout(
            title=f"3D Mine View - {view_mode}",
            scene=dict(
                xaxis_title="X Coordinate (m)",
                yaxis_title="Y Coordinate (m)",
                zaxis_title="Elevation (m)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
            ),
            width=900,
            height=700
        )
        
        return fig
    
    def _add_geological_layers(self, fig, mine_data):
        """Add geological layer visualization"""
        # Simulate geological layers
        zones = mine_data['zones']
        layer_colors = {
            'limestone': '#E6E6FA',
            'sandstone': '#F4A460', 
            'shale': '#708090',
            'granite': '#696969'
        }
        
        for zone in zones:
            geo_type = zone.get('geological_type', 'unknown')
            center = zone['center_coordinates']
            
            # Create geological formation representation
            theta = np.linspace(0, 2*np.pi, 12)
            radius = 60
            
            for layer in range(3):  # 3 geological layers
                layer_x = center['x'] + radius * np.cos(theta)
                layer_y = center['y'] + radius * np.sin(theta)
                layer_z = np.full_like(layer_x, center['z'] - layer * 20)
                
                fig.add_trace(go.Scatter3d(
                    x=layer_x,
                    y=layer_y,
                    z=layer_z,
                    mode='lines',
                    line=dict(
                        color=layer_colors.get(geo_type, 'gray'),
                        width=6 - layer
                    ),
                    opacity=0.6 - layer * 0.1,
                    name=f"{geo_type.title()} Layer {layer+1}" if layer == 0 else "",
                    showlegend=layer == 0,
                    hovertemplate=f"Geological Layer: {geo_type}<br>Depth: {layer * 20}m<extra></extra>"
                ))
    
    def create_risk_heatmap_2d(self, sensor_data):
        """Create 2D risk heatmap overlay"""
        # Extract sensor positions and risk levels
        x_coords = []
        y_coords = []
        risk_levels = []
        
        for sensor in sensor_data:
            if 'coordinates' in sensor:
                x_coords.append(sensor['coordinates'].get('lat', 0))
                y_coords.append(sensor['coordinates'].get('lon', 0))
                risk_levels.append(sensor.get('risk_probability', 0))
        
        # Create heatmap
        fig = go.Figure(data=go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers',
            marker=dict(
                size=risk_levels,
                color=risk_levels,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="Risk Level"),
                sizemode='diameter',
                sizeref=0.02,
                sizemin=5
            ),
            text=[f"Sensor {s['id']}: {s['risk_probability']:.1%}" for s in sensor_data],
            hovertemplate='%{text}<br>Coordinates: (%{x:.3f}, %{y:.3f})<extra></extra>'
        ))
        
        fig.update_layout(
            title="Mine Risk Heatmap",
            xaxis_title="Latitude",
            yaxis_title="Longitude",
            width=800,
            height=600
        )
        
        return fig