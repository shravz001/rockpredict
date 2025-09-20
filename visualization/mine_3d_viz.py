import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime

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
        
        # Configure layout
        fig.update_layout(
            title="3D Mine Visualization with Risk Assessment",
            scene=dict(
                xaxis_title="X Coordinate (m)",
                yaxis_title="Y Coordinate (m)",
                zaxis_title="Elevation (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                ),
                aspectmode='manual',
                aspectratio=dict(x=1, y=0.8, z=0.6)
            ),
            width=900,
            height=700,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        return fig
    
    def _add_risk_zone(self, fig, zone):
        """Add risk zone visualization to the figure"""
        # Create circular risk zone overlay
        center = zone['center_coordinates']
        risk_level = zone['risk_level']
        
        # Determine color based on risk level
        if risk_level >= 0.85:
            color = 'red'
            opacity = 0.8
        elif risk_level >= 0.7:
            color = 'orange'
            opacity = 0.6
        elif risk_level >= 0.3:
            color = 'yellow'
            opacity = 0.4
        else:
            color = 'green'
            opacity = 0.3
        
        # Create zone boundary
        theta = np.linspace(0, 2*np.pi, 20)
        radius = 80  # meters
        zone_x = center['x'] + radius * np.cos(theta)
        zone_y = center['y'] + radius * np.sin(theta)
        zone_z = np.full_like(zone_x, center['z'] + 5)  # Slightly above terrain
        
        fig.add_trace(go.Scatter3d(
            x=zone_x,
            y=zone_y,
            z=zone_z,
            mode='lines',
            line=dict(color=color, width=8),
            opacity=opacity,
            name=f"{zone['name']} (Risk: {risk_level:.2f})",
            hovertemplate=f"Zone: {zone['name']}<br>Risk Level: {risk_level:.2%}<br>Type: {zone.get('geological_type', 'Unknown')}<extra></extra>"
        ))
        
        # Add zone center marker
        fig.add_trace(go.Scatter3d(
            x=[center['x']],
            y=[center['y']],
            z=[center['z'] + 10],
            mode='markers+text',
            marker=dict(
                size=12,
                color=color,
                symbol='diamond',
                opacity=0.9
            ),
            text=[zone['name']],
            textposition='top center',
            name=f"{zone['name']} Center",
            showlegend=False,
            hovertemplate=f"Zone Center: {zone['name']}<br>Coordinates: ({center['x']:.0f}, {center['y']:.0f}, {center['z']:.0f})<br>Geological Type: {zone.get('geological_type', 'Unknown')}<extra></extra>"
        ))
    
    def _add_sensor_network(self, fig, sensors):
        """Add sensor network to the visualization"""
        sensor_types = {}
        
        # Group sensors by type for different visualization
        for sensor in sensors:
            sensor_type = sensor['type']
            if sensor_type not in sensor_types:
                sensor_types[sensor_type] = []
            sensor_types[sensor_type].append(sensor)
        
        # Color mapping for sensor types
        type_colors = {
            'displacement': 'blue',
            'strain': 'purple',
            'pressure': 'cyan',
            'vibration': 'magenta',
            'tilt': 'brown'
        }
        
        # Symbols for sensor types
        type_symbols = {
            'displacement': 'circle',
            'strain': 'square',
            'pressure': 'diamond',
            'vibration': 'cross',
            'tilt': 'x'
        }
        
        for sensor_type, type_sensors in sensor_types.items():
            x_coords = [s['coordinates']['x'] for s in type_sensors]
            y_coords = [s['coordinates']['y'] for s in type_sensors]
            z_coords = [s['coordinates']['z'] for s in type_sensors]
            sensor_ids = [s['id'] for s in type_sensors]
            battery_levels = [s.get('battery_level', 100) for s in type_sensors]
            signal_strengths = [s.get('signal_strength', -80) for s in type_sensors]
            
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    size=8,
                    color=type_colors.get(sensor_type, 'gray'),
                    symbol=type_symbols.get(sensor_type, 'circle'),
                    opacity=0.8
                ),
                name=f"{sensor_type.title()} Sensors",
                text=sensor_ids,
                hovertemplate="Sensor: %{text}<br>Type: " + sensor_type + "<br>Battery: %{customdata[0]:.0f}%<br>Signal: %{customdata[1]:.0f} dBm<extra></extra>",
                customdata=list(zip(battery_levels, signal_strengths))
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