import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json

class DataGenerator:
    def __init__(self):
        self.base_stability = 0.8
        self.sensor_locations = self._generate_sensor_locations()
        
    def _generate_sensor_locations(self):
        """Generate realistic sensor locations for the mine"""
        locations = []
        for i in range(50):
            locations.append({
                'id': f'SENSOR_{i+1:03d}',
                'type': random.choice(['displacement', 'strain', 'pore_pressure', 'vibration']),
                'x': random.uniform(-500, 500),
                'y': random.uniform(-300, 300),
                'z': random.uniform(0, 200),
                'status': random.choice(['Online', 'Online', 'Online', 'Warning', 'Offline']),
                'last_reading': datetime.now() - timedelta(minutes=random.randint(1, 30))
            })
        return locations
    
    def generate_realtime_data(self):
        """Generate current real-time sensor data"""
        # Environmental factors
        temperature = random.uniform(15, 35)  # Celsius
        humidity = random.uniform(30, 80)     # Percentage
        rainfall_24h = max(0, random.gauss(5, 10))  # mm
        wind_speed = random.uniform(0, 20)    # km/h
        
        # Geotechnical data
        displacement_readings = [random.gauss(0, 2) for _ in range(10)]  # mm
        strain_readings = [random.gauss(100, 50) for _ in range(10)]     # microstrain
        pore_pressure = [random.gauss(50, 20) for _ in range(10)]        # kPa
        vibration_amplitude = random.uniform(0, 5)                       # mm/s
        
        # Calculate stability index
        stability_factors = [
            max(0, 1 - rainfall_24h / 50),  # Less stable with more rain
            max(0, 1 - max(displacement_readings) / 10),  # Less stable with more displacement
            max(0, 1 - vibration_amplitude / 10),  # Less stable with more vibration
            random.uniform(0.7, 1.0)  # Random geological factor
        ]
        stability_index = np.mean(stability_factors)
        
        # Active sensors count
        active_sensors = sum(1 for loc in self.sensor_locations if loc['status'] == 'Online')
        
        # GPS coordinates (example mine location)
        gps_lat = -23.5505 + random.uniform(-0.01, 0.01)  # São Paulo region
        gps_lon = -46.6333 + random.uniform(-0.01, 0.01)
        
        return {
            'timestamp': datetime.now(),
            'temperature': temperature,
            'humidity': humidity,
            'rainfall_24h': rainfall_24h,
            'wind_speed': wind_speed,
            'displacement_readings': displacement_readings,
            'strain_readings': strain_readings,
            'pore_pressure': pore_pressure,
            'vibration_amplitude': vibration_amplitude,
            'stability_index': stability_index,
            'active_sensors': active_sensors,
            'gps_lat': gps_lat,
            'gps_lon': gps_lon,
            'location': f'Zone A-{random.randint(1, 10)}'
        }
    
    def generate_risk_history(self, hours=24):
        """Generate historical risk data"""
        timestamps = []
        risk_levels = []
        
        for i in range(hours * 6):  # Every 10 minutes
            timestamp = datetime.now() - timedelta(minutes=i * 10)
            timestamps.append(timestamp)
            
            # Simulate risk fluctuation with some patterns
            base_risk = 30 + 20 * np.sin(i * 0.1)  # Daily cycle
            noise = random.gauss(0, 10)
            seasonal_factor = 10 * np.sin(i * 0.01)  # Longer term trends
            
            risk = max(0, min(100, base_risk + noise + seasonal_factor))
            risk_levels.append(risk)
        
        timestamps.reverse()
        risk_levels.reverse()
        
        return {
            'timestamps': timestamps,
            'risk_levels': risk_levels
        }
    
    def generate_environmental_data(self, hours=24):
        """Generate environmental monitoring data"""
        timestamps = []
        temperature = []
        humidity = []
        
        for i in range(hours * 4):  # Every 15 minutes
            timestamp = datetime.now() - timedelta(minutes=i * 15)
            timestamps.append(timestamp)
            
            # Daily temperature cycle
            hour_of_day = timestamp.hour
            base_temp = 20 + 10 * np.sin((hour_of_day - 6) * np.pi / 12)
            temp_noise = random.gauss(0, 2)
            temperature.append(max(0, base_temp + temp_noise))
            
            # Humidity inversely related to temperature
            base_humidity = 80 - (base_temp - 20) * 2
            hum_noise = random.gauss(0, 5)
            humidity.append(max(20, min(100, base_humidity + hum_noise)))
        
        timestamps.reverse()
        temperature.reverse()
        humidity.reverse()
        
        return {
            'timestamps': timestamps,
            'temperature': temperature,
            'humidity': humidity
        }
    
    def generate_sensor_status(self):
        """Generate current sensor status data"""
        sensor_data = []
        
        for sensor in self.sensor_locations:
            # Generate realistic readings based on sensor type
            if sensor['type'] == 'displacement':
                value = f"{random.gauss(0, 2):.2f} mm"
                unit = "mm"
            elif sensor['type'] == 'strain':
                value = f"{random.gauss(100, 50):.0f} μστ"
                unit = "microstrain"
            elif sensor['type'] == 'pore_pressure':
                value = f"{random.gauss(50, 20):.1f} kPa"
                unit = "kPa"
            elif sensor['type'] == 'vibration':
                value = f"{random.uniform(0, 5):.2f} mm/s"
                unit = "mm/s"
            
            # Battery level (only for wireless sensors)
            battery = random.randint(20, 100) if random.random() > 0.3 else None
            
            sensor_data.append({
                'Sensor ID': sensor['id'],
                'Type': sensor['type'].replace('_', ' ').title(),
                'Location': f"({sensor['x']:.0f}, {sensor['y']:.0f}, {sensor['z']:.0f})",
                'Status': sensor['status'],
                'Current Value': value,
                'Battery (%)': f"{battery}%" if battery else "N/A",
                'Last Update': sensor['last_reading'].strftime("%H:%M:%S")
            })
        
        return sensor_data
    
    def generate_3d_mine_data(self, view_mode="Risk Overlay", time_range="Real-time", 
                             show_sensors=True, show_risk_zones=True):
        """Generate 3D mine terrain and risk data"""
        # Create terrain mesh
        x = np.linspace(-500, 500, 50)
        y = np.linspace(-300, 300, 30)
        X, Y = np.meshgrid(x, y)
        
        # Generate realistic mine pit terrain
        center_x, center_y = 0, 0
        distance_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        
        # Create pit-like depression
        Z = 200 - (distance_from_center / 3) - 20 * np.sin(X/100) * np.cos(Y/100)
        
        # Add some randomness for realistic terrain
        Z += np.random.normal(0, 5, Z.shape)
        
        # Generate risk overlay data
        if show_risk_zones:
            # Risk is higher near steep slopes and water accumulation areas
            gradient_x = np.gradient(Z, axis=1)
            gradient_y = np.gradient(Z, axis=0)
            slope = np.sqrt(gradient_x**2 + gradient_y**2)
            
            # Higher risk for steeper slopes
            risk_base = (slope / np.max(slope)) * 50
            
            # Add some random risk hotspots
            for _ in range(5):
                hot_x = random.uniform(-400, 400)
                hot_y = random.uniform(-200, 200)
                hotspot = 40 * np.exp(-((X - hot_x)**2 + (Y - hot_y)**2) / 10000)
                risk_base += hotspot
            
            risk_overlay = np.clip(risk_base, 0, 100)
        else:
            risk_overlay = np.zeros_like(Z)
        
        # Sensor positions for visualization
        sensor_positions = []
        if show_sensors:
            for sensor in self.sensor_locations[:20]:  # Show subset for clarity
                sensor_positions.append({
                    'x': sensor['x'],
                    'y': sensor['y'],
                    'z': sensor['z'],
                    'type': sensor['type'],
                    'status': sensor['status'],
                    'id': sensor['id']
                })
        
        return {
            'terrain': {'X': X, 'Y': Y, 'Z': Z},
            'risk_overlay': risk_overlay,
            'sensors': sensor_positions,
            'view_mode': view_mode,
            'time_range': time_range
        }
    
    def generate_historical_analysis(self, period):
        """Generate historical data for analysis"""
        if period == "Last 7 Days":
            days = 7
        elif period == "Last 30 Days":
            days = 30
        elif period == "Last 3 Months":
            days = 90
        else:  # Last Year
            days = 365
        
        # Risk level distribution
        risk_levels = []
        for _ in range(days * 24):  # Hourly data
            base_risk = random.uniform(20, 60)
            seasonal = 10 * np.sin((_ / (24 * 30)) * 2 * np.pi)  # Monthly cycle
            weather_impact = random.uniform(-15, 25)  # Weather events
            risk = max(0, min(100, base_risk + seasonal + weather_impact))
            risk_levels.append(risk)
        
        # Alert frequency
        alert_dates = []
        alert_counts = []
        for i in range(days):
            date = datetime.now().date() - timedelta(days=days-i-1)
            alert_dates.append(date)
            
            # More alerts during high-risk periods
            daily_risk = np.mean(risk_levels[i*24:(i+1)*24])
            alert_probability = max(0, (daily_risk - 50) / 50)
            num_alerts = np.random.poisson(alert_probability * 5)
            alert_counts.append(num_alerts)
        
        return {
            'risk_levels': risk_levels,
            'alert_dates': alert_dates,
            'alert_counts': alert_counts
        }
    
    def generate_dem_data(self, size=(100, 100)):
        """Generate Digital Elevation Model data"""
        x = np.linspace(-1000, 1000, size[0])
        y = np.linspace(-600, 600, size[1])
        X, Y = np.meshgrid(x, y)
        
        # Create realistic mining terrain with multiple benches
        Z = np.zeros_like(X)
        
        # Main pit
        center_distance = np.sqrt(X**2 + Y**2)
        Z = 300 - center_distance / 4
        
        # Add mining benches (stepped levels)
        for level in range(50, 250, 30):
            mask = (Z > level) & (Z < level + 15)
            Z[mask] = level
        
        # Add some geological variation
        Z += 20 * np.sin(X / 200) * np.cos(Y / 150)
        Z += np.random.normal(0, 2, Z.shape)
        
        return {'X': X, 'Y': Y, 'Z': Z}
    
    def generate_drone_imagery_features(self):
        """Simulate drone imagery analysis features"""
        features = []
        
        # Simulate detected features from drone imagery
        feature_types = ['crack', 'loose_rock', 'vegetation_change', 'water_seepage', 'shadow_anomaly']
        
        for i in range(random.randint(5, 15)):
            feature = {
                'id': f'FEAT_{i+1:03d}',
                'type': random.choice(feature_types),
                'confidence': random.uniform(0.6, 0.95),
                'x': random.uniform(-500, 500),
                'y': random.uniform(-300, 300),
                'area': random.uniform(1, 50),  # square meters
                'severity': random.choice(['Low', 'Medium', 'High']),
                'timestamp': datetime.now() - timedelta(hours=random.randint(0, 24))
            }
            features.append(feature)
        
        return features
