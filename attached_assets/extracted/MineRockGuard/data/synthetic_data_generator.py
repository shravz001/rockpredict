import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json

class SyntheticDataGenerator:
    def __init__(self):
        self.sensor_count = 47
        self.zone_count = 12
        self.base_coordinates = {'lat': 45.123, 'lon': -123.456}
        
    def generate_real_time_data(self):
        """Generate current sensor readings and environmental data"""
        current_time = datetime.now()
        
        # Generate sensor data
        sensors = []
        for i in range(self.sensor_count):
            # Base risk varies by sensor location and time
            base_risk = 0.2 + 0.3 * np.sin(i * np.pi / 10) + 0.1 * np.sin(current_time.hour * np.pi / 12)
            noise = np.random.normal(0, 0.15)
            risk_probability = max(0, min(1, base_risk + noise))
            
            sensor_data = {
                'id': f"S{i+1:03d}",
                'zone': f"Zone_{(i // 4) + 1}",
                'coordinates': {
                    'lat': self.base_coordinates['lat'] + np.random.uniform(-0.01, 0.01),
                    'lon': self.base_coordinates['lon'] + np.random.uniform(-0.01, 0.01),
                    'elevation': 1200 + np.random.uniform(-100, 200)
                },
                'displacement_rate': np.random.uniform(0.1, 2.5),  # mm/day
                'strain_magnitude': np.random.uniform(0.05, 1.2),  # microstrains
                'pore_pressure': np.random.uniform(50, 150),  # kPa
                'vibration_level': np.random.uniform(0, 0.8),  # g-force
                'crack_density': np.random.uniform(0, 0.6),  # cracks/m²
                'soil_moisture': np.random.uniform(10, 40),  # %
                'slope_angle': np.random.uniform(35, 75),  # degrees
                'risk_probability': risk_probability,
                'status': 'online' if np.random.random() > 0.05 else 'offline',
                'last_update': current_time - timedelta(minutes=np.random.randint(0, 5))
            }
            sensors.append(sensor_data)
        
        # Generate environmental data
        environmental = {
            'temperature': np.random.normal(15, 10),  # Celsius
            'rainfall': max(0, np.random.gamma(2, 2)),  # mm/hour
            'wind_speed': max(0, np.random.gamma(3, 2)),  # m/s
            'wind_direction': np.random.uniform(0, 360),  # degrees
            'humidity': np.random.uniform(30, 95),  # %
            'atmospheric_pressure': np.random.normal(1013, 20),  # hPa
            'solar_radiation': max(0, np.random.gamma(5, 100)),  # W/m²
            'timestamp': current_time
        }
        
        # Generate DEM data (simplified)
        dem_data = self.generate_dem_data()
        
        return {
            'sensors': sensors,
            'environmental': environmental,
            'dem': dem_data,
            'timestamp': current_time
        }
    
    def generate_dem_data(self):
        """Generate Digital Elevation Model data"""
        # Create a grid representing the mine topology
        grid_size = 50
        x = np.linspace(0, 1000, grid_size)  # meters
        y = np.linspace(0, 800, grid_size)   # meters
        X, Y = np.meshgrid(x, y)
        
        # Create realistic mine pit topology
        # Central depression with terraced sides
        center_x, center_y = 500, 400
        distance_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        
        # Base elevation with pit
        Z = 1300 - 0.3 * distance_from_center  # Gradual slope down to pit
        
        # Add terraces (benches) typical in open pit mines
        terrace_height = 15  # meters between benches
        Z = np.floor(Z / terrace_height) * terrace_height
        
        # Add some geological variation
        Z += 5 * np.sin(X / 100) * np.cos(Y / 80)
        Z += np.random.normal(0, 2, Z.shape)  # Surface roughness
        
        return {
            'x': X.tolist(),
            'y': Y.tolist(),
            'z': Z.tolist(),
            'grid_size': grid_size,
            'resolution': 20  # meters per grid cell
        }
    
    def generate_mine_topology(self):
        """Generate detailed 3D mine topology data"""
        # Generate mine structure with multiple zones
        zones = []
        
        for zone_id in range(1, self.zone_count + 1):
            # Random zone positioning around the mine
            angle = (zone_id - 1) * 2 * np.pi / self.zone_count
            zone_x = 500 + 300 * np.cos(angle)
            zone_y = 400 + 200 * np.sin(angle)
            
            # Zone-specific risk level
            base_risk = np.random.uniform(0.1, 0.8)
            
            zone_data = {
                'id': zone_id,
                'name': f"Zone_{zone_id}",
                'center_coordinates': {'x': zone_x, 'y': zone_y, 'z': 1250 + np.random.uniform(-50, 50)},
                'risk_level': base_risk,
                'geological_type': np.random.choice(['limestone', 'sandstone', 'shale', 'granite']),
                'slope_stability': np.random.uniform(0.3, 0.9),
                'sensor_count': np.random.randint(2, 6),
                'last_incident': datetime.now() - timedelta(days=np.random.randint(1, 365)) if np.random.random() > 0.7 else None
            }
            zones.append(zone_data)
        
        # Generate detailed DEM
        dem_data = self.generate_dem_data()
        
        # Add sensor network
        sensor_network = self.generate_sensor_network()
        
        return {
            'zones': zones,
            'dem': dem_data,
            'sensor_network': sensor_network,
            'mine_parameters': {
                'total_area': 800000,  # m²
                'max_depth': 200,      # meters
                'active_benches': 12,
                'access_roads': 8,
                'equipment_zones': 15
            }
        }
    
    def generate_sensor_network(self):
        """Generate sensor network topology"""
        sensors = []
        
        for i in range(self.sensor_count):
            # Distribute sensors across the mine area
            x = np.random.uniform(50, 950)
            y = np.random.uniform(50, 750)
            z = 1200 + np.random.uniform(0, 100)
            
            sensor = {
                'id': f"S{i+1:03d}",
                'type': np.random.choice(['displacement', 'strain', 'pressure', 'vibration', 'tilt']),
                'coordinates': {'x': x, 'y': y, 'z': z},
                'communication_type': np.random.choice(['LoRaWAN', 'radio', 'wired']),
                'battery_level': np.random.uniform(20, 100) if np.random.choice(['LoRaWAN', 'radio']) else 100,
                'signal_strength': np.random.uniform(-120, -70),  # dBm
                'installation_date': datetime.now() - timedelta(days=np.random.randint(30, 730)),
                'maintenance_due': datetime.now() + timedelta(days=np.random.randint(1, 90))
            }
            sensors.append(sensor)
        
        return sensors
    
    def generate_drone_imagery_data(self):
        """Generate synthetic drone imagery analysis data"""
        flights = []
        
        # Generate recent drone flights
        for i in range(10):
            flight_time = datetime.now() - timedelta(hours=np.random.randint(1, 72))
            
            flight_data = {
                'flight_id': f"DRONE_{i+1:03d}",
                'timestamp': flight_time,
                'coverage_area': {
                    'zones_covered': np.random.choice(range(1, self.zone_count+1), size=np.random.randint(3, 8), replace=False).tolist()
                },
                'image_analysis': {
                    'total_images': np.random.randint(150, 500),
                    'crack_detection_count': np.random.randint(5, 25),
                    'vegetation_health': np.random.uniform(0.6, 0.95),
                    'surface_changes_detected': np.random.randint(2, 12),
                    'weather_conditions': np.random.choice(['clear', 'partly_cloudy', 'overcast', 'light_rain'])
                },
                'risk_indicators': {
                    'new_cracks': np.random.randint(0, 5),
                    'rock_displacement': np.random.uniform(0, 15),  # mm
                    'erosion_detected': np.random.choice([True, False]),
                    'overall_risk_score': np.random.uniform(0.2, 0.8)
                }
            }
            flights.append(flight_data)
        
        return flights
    
    def generate_historical_sensor_data(self, days=30):
        """Generate historical sensor data for trend analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate hourly data points
        time_points = []
        current = start_date
        while current <= end_date:
            time_points.append(current)
            current += timedelta(hours=1)
        
        historical_data = []
        
        for timestamp in time_points:
            # Simulate daily and seasonal patterns
            hour_factor = np.sin(timestamp.hour * np.pi / 12)
            day_factor = np.sin(timestamp.timetuple().tm_yday * 2 * np.pi / 365)
            
            # Generate sensor readings for this timestamp
            for sensor_id in range(1, self.sensor_count + 1):
                base_reading = 0.3 + 0.2 * hour_factor + 0.1 * day_factor
                noise = np.random.normal(0, 0.1)
                risk_level = max(0, min(1, base_reading + noise))
                
                reading = {
                    'timestamp': timestamp,
                    'sensor_id': f"S{sensor_id:03d}",
                    'displacement_rate': np.random.uniform(0.1, 2.0),
                    'strain_magnitude': np.random.uniform(0.05, 1.0),
                    'pore_pressure': np.random.uniform(50, 140),
                    'temperature': 15 + 10 * np.sin((timestamp.timetuple().tm_yday + timestamp.hour/24) * 2 * np.pi / 365) + np.random.normal(0, 2),
                    'rainfall': max(0, np.random.gamma(2, 2)) if np.random.random() > 0.7 else 0,
                    'wind_speed': max(0, np.random.gamma(3, 2)),
                    'vibration_level': np.random.uniform(0, 0.6),
                    'risk_probability': risk_level,
                    'alert_triggered': risk_level > 0.7
                }
                historical_data.append(reading)
        
        return historical_data
