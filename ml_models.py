import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
import os
from datetime import datetime, timedelta
import random

class RockfallPredictor:
    def __init__(self):
        self.rf_classifier = None
        self.xgb_classifier = None
        self.rf_regressor = None
        self.xgb_regressor = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            'temperature', 'humidity', 'rainfall_24h', 'wind_speed',
            'avg_displacement', 'max_displacement', 'avg_strain', 'max_strain',
            'avg_pore_pressure', 'max_pore_pressure', 'vibration_amplitude',
            'slope_angle', 'soil_moisture', 'previous_risk'
        ]
        
        # Initialize and train models with synthetic data
        self._train_initial_models()
    
    def _generate_synthetic_training_data(self, n_samples=5000):
        """Generate synthetic training data for the models"""
        np.random.seed(42)  # For reproducibility
        
        data = []
        labels = []
        
        for _ in range(n_samples):
            # Environmental features
            temperature = np.random.normal(25, 8)
            humidity = np.random.normal(60, 20)
            rainfall_24h = np.random.exponential(5)
            wind_speed = np.random.exponential(10)
            
            # Geotechnical features
            avg_displacement = np.random.normal(0, 3)
            max_displacement = avg_displacement + np.random.exponential(2)
            avg_strain = np.random.normal(100, 40)
            max_strain = avg_strain + np.random.exponential(50)
            avg_pore_pressure = np.random.normal(50, 25)
            max_pore_pressure = avg_pore_pressure + np.random.exponential(20)
            vibration_amplitude = np.random.exponential(2)
            
            # Geological features
            slope_angle = np.random.uniform(30, 70)
            soil_moisture = np.random.normal(30, 15)
            previous_risk = np.random.uniform(0, 100)
            
            # Create risk calculation with realistic relationships
            risk_factors = [
                rainfall_24h * 2,  # Rain increases risk
                max_displacement * 5,  # Large displacements increase risk
                vibration_amplitude * 8,  # Vibrations increase risk
                (slope_angle - 45) * 2,  # Steeper slopes increase risk
                soil_moisture * 0.5,  # Wet soil increases risk
                previous_risk * 0.3,  # Previous risk influences current risk
                max_strain * 0.1,  # High strain increases risk
                max_pore_pressure * 0.3  # High pore pressure increases risk
            ]
            
            base_risk = sum(max(0, factor) for factor in risk_factors)
            noise = np.random.normal(0, 10)
            risk_level = max(0, min(100, base_risk + noise))
            
            # Convert to classification labels
            if risk_level < 30:
                risk_class = 0  # Low risk
            elif risk_level < 60:
                risk_class = 1  # Medium risk
            elif risk_level < 80:
                risk_class = 2  # High risk
            else:
                risk_class = 3  # Critical risk
            
            features = [
                temperature, humidity, rainfall_24h, wind_speed,
                avg_displacement, max_displacement, avg_strain, max_strain,
                avg_pore_pressure, max_pore_pressure, vibration_amplitude,
                slope_angle, soil_moisture, previous_risk
            ]
            
            data.append(features)
            labels.append((risk_class, risk_level))
        
        X = np.array(data)
        y_class = np.array([label[0] for label in labels])
        y_reg = np.array([label[1] for label in labels])
        
        return X, y_class, y_reg
    
    def _train_initial_models(self):
        """Train initial models with synthetic data"""
        X, y_class, y_reg = self._generate_synthetic_training_data()
        
        # Split data
        X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
            X, y_class, y_reg, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest models
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            random_state=42
        )
        self.rf_regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            random_state=42
        )
        
        self.rf_classifier.fit(X_train_scaled, y_class_train)
        self.rf_regressor.fit(X_train_scaled, y_reg_train)
        
        # Train XGBoost models
        self.xgb_classifier = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        self.xgb_regressor = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        self.xgb_classifier.fit(X_train_scaled, y_class_train)
        self.xgb_regressor.fit(X_train_scaled, y_reg_train)
        
        self.is_trained = True
        
        # Store test data for metrics
        self.X_test = X_test_scaled
        self.y_class_test = y_class_test
        self.y_reg_test = y_reg_test
    
    def predict_risk(self, sensor_data):
        """Predict risk level from sensor data"""
        if not self.is_trained:
            self._train_initial_models()
        
        # Extract features from sensor data
        features = self._extract_features(sensor_data)
        features_scaled = self.scaler.transform([features])
        
        # Get predictions from both models
        rf_risk = self.rf_regressor.predict(features_scaled)[0]
        xgb_risk = self.xgb_regressor.predict(features_scaled)[0]
        
        # Ensemble prediction (average)
        predicted_risk = (rf_risk + xgb_risk) / 2
        
        return max(0, min(100, predicted_risk))
    
    def predict_risk_class(self, sensor_data):
        """Predict risk class from sensor data"""
        if not self.is_trained:
            self._train_initial_models()
        
        features = self._extract_features(sensor_data)
        features_scaled = self.scaler.transform([features])
        
        rf_class = self.rf_classifier.predict(features_scaled)[0]
        xgb_class = self.xgb_classifier.predict(features_scaled)[0]
        
        # Return the more conservative (higher risk) prediction
        return max(rf_class, xgb_class)
    
    def _extract_features(self, sensor_data):
        """Extract features from raw sensor data"""
        # Calculate statistical features from sensor readings
        displacement_readings = sensor_data.get('displacement_readings', [0])
        strain_readings = sensor_data.get('strain_readings', [100])
        pore_pressure_readings = sensor_data.get('pore_pressure', [50])
        
        features = [
            sensor_data.get('temperature', 25),
            sensor_data.get('humidity', 60),
            sensor_data.get('rainfall_24h', 0),
            sensor_data.get('wind_speed', 5),
            np.mean(displacement_readings),
            np.max(displacement_readings),
            np.mean(strain_readings),
            np.max(strain_readings),
            np.mean(pore_pressure_readings),
            np.max(pore_pressure_readings),
            sensor_data.get('vibration_amplitude', 1),
            random.uniform(35, 65),  # slope_angle (would come from DEM analysis)
            sensor_data.get('humidity', 60) * 0.5,  # soil_moisture estimate
            random.uniform(20, 70)  # previous_risk (would come from historical data)
        ]
        
        return features
    
    def get_model_metrics(self):
        """Get performance metrics for both models"""
        if not self.is_trained:
            return {}
        
        # Get predictions
        rf_class_pred = self.rf_classifier.predict(self.X_test)
        xgb_class_pred = self.xgb_classifier.predict(self.X_test)
        
        # Calculate metrics
        metrics = {
            'rf_accuracy': accuracy_score(self.y_class_test, rf_class_pred),
            'rf_precision': precision_score(self.y_class_test, rf_class_pred, average='weighted'),
            'rf_recall': recall_score(self.y_class_test, rf_class_pred, average='weighted'),
            'rf_f1': f1_score(self.y_class_test, rf_class_pred, average='weighted'),
            'xgb_accuracy': accuracy_score(self.y_class_test, xgb_class_pred),
            'xgb_precision': precision_score(self.y_class_test, xgb_class_pred, average='weighted'),
            'xgb_recall': recall_score(self.y_class_test, xgb_class_pred, average='weighted'),
            'xgb_f1': f1_score(self.y_class_test, xgb_class_pred, average='weighted')
        }
        
        return metrics
    
    def generate_forecast(self, hours=48):
        """Generate risk forecast for the next specified hours"""
        timestamps = []
        predicted_risk = []
        upper_bound = []
        lower_bound = []
        
        # Base current risk
        current_risk = random.uniform(30, 70)
        
        for i in range(hours):
            timestamp = datetime.now() + timedelta(hours=i)
            timestamps.append(timestamp)
            
            # Add some temporal patterns
            daily_cycle = 10 * np.sin((timestamp.hour - 12) * np.pi / 12)
            weather_trend = 5 * np.sin(i * 0.1)
            random_variation = random.gauss(0, 5)
            
            risk = current_risk + daily_cycle + weather_trend + random_variation
            risk = max(0, min(100, risk))
            
            predicted_risk.append(risk)
            
            # Add confidence intervals
            confidence_width = 15
            upper_bound.append(min(100, risk + confidence_width))
            lower_bound.append(max(0, risk - confidence_width))
            
            # Update current risk for next iteration
            current_risk = risk
        
        return {
            'timestamps': timestamps,
            'predicted_risk': predicted_risk,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound
        }
    
    def get_feature_importance(self):
        """Get feature importance from both models"""
        if not self.is_trained:
            return {}
        
        # Get Random Forest feature importance
        rf_importance = self.rf_regressor.feature_importances_
        
        # Get XGBoost feature importance
        xgb_importance = self.xgb_regressor.feature_importances_
        
        # Average importance
        avg_importance = (rf_importance + xgb_importance) / 2
        
        # Sort by importance
        importance_pairs = list(zip(self.feature_names, avg_importance))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'features': [pair[0] for pair in importance_pairs],
            'importance': [pair[1] for pair in importance_pairs]
        }
    
    def get_correlation_matrix(self):
        """Get correlation matrix of features"""
        # Generate sample data for correlation analysis
        X, _, _ = self._generate_synthetic_training_data(1000)
        df = pd.DataFrame(X, columns=self.feature_names)
        correlation_matrix = df.corr().values
        
        return {
            'matrix': correlation_matrix,
            'features': self.feature_names
        }
    
    def update_rf_config(self, config):
        """Update Random Forest configuration"""
        self.rf_classifier = RandomForestClassifier(
            n_estimators=config['n_estimators'],
            max_depth=config['max_depth'],
            min_samples_split=config['min_samples_split'],
            random_state=42
        )
        self.rf_regressor = RandomForestRegressor(
            n_estimators=config['n_estimators'],
            max_depth=config['max_depth'],
            min_samples_split=config['min_samples_split'],
            random_state=42
        )
        # Retrain with new configuration
        self._retrain_models()
    
    def update_xgb_config(self, config):
        """Update XGBoost configuration"""
        self.xgb_classifier = xgb.XGBClassifier(
            n_estimators=config['n_estimators'],
            max_depth=config['max_depth'],
            learning_rate=config['learning_rate'],
            random_state=42
        )
        self.xgb_regressor = xgb.XGBRegressor(
            n_estimators=config['n_estimators'],
            max_depth=config['max_depth'],
            learning_rate=config['learning_rate'],
            random_state=42
        )
        # Retrain with new configuration
        self._retrain_models()
    
    def _retrain_models(self):
        """Retrain models with current configuration"""
        X, y_class, y_reg = self._generate_synthetic_training_data()
        X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
            X, y_class, y_reg, test_size=0.2, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.rf_classifier.fit(X_train_scaled, y_class_train)
        self.rf_regressor.fit(X_train_scaled, y_reg_train)
        self.xgb_classifier.fit(X_train_scaled, y_class_train)
        self.xgb_regressor.fit(X_train_scaled, y_reg_train)
        
        self.X_test = X_test_scaled
        self.y_class_test = y_class_test
        self.y_reg_test = y_reg_test
    
    def save_models(self, directory="models"):
        """Save trained models to disk"""
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        joblib.dump(self.rf_classifier, os.path.join(directory, "rf_classifier.pkl"))
        joblib.dump(self.rf_regressor, os.path.join(directory, "rf_regressor.pkl"))
        joblib.dump(self.xgb_classifier, os.path.join(directory, "xgb_classifier.pkl"))
        joblib.dump(self.xgb_regressor, os.path.join(directory, "xgb_regressor.pkl"))
        joblib.dump(self.scaler, os.path.join(directory, "scaler.pkl"))
    
    def load_models(self, directory="models"):
        """Load trained models from disk"""
        try:
            self.rf_classifier = joblib.load(os.path.join(directory, "rf_classifier.pkl"))
            self.rf_regressor = joblib.load(os.path.join(directory, "rf_regressor.pkl"))
            self.xgb_classifier = joblib.load(os.path.join(directory, "xgb_classifier.pkl"))
            self.xgb_regressor = joblib.load(os.path.join(directory, "xgb_regressor.pkl"))
            self.scaler = joblib.load(os.path.join(directory, "scaler.pkl"))
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
