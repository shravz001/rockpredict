import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

class RockfallPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'displacement_rate', 'strain_magnitude', 'pore_pressure',
            'temperature', 'rainfall', 'wind_speed', 'vibration_level',
            'slope_angle', 'soil_moisture', 'crack_density'
        ]
        self.model_metrics = {'accuracy': 0.85, 'precision': 0.82, 'recall': 0.88}
        self.feature_importance = {}
        self.initialize_model()
        
        # Initialize OpenAI for advanced analysis
        self.openai_client = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def initialize_model(self):
        """Initialize the ensemble machine learning model"""
        # Create ensemble model
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        nn_model = MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=1000)
        svm_model = SVC(probability=True, random_state=42)
        
        self.model = VotingClassifier(
            estimators=[('rf', rf_model), ('nn', nn_model), ('svm', svm_model)],
            voting='soft'
        )
        
        # Train with synthetic data
        self._train_initial_model()
    
    def _train_initial_model(self):
        """Train the model with synthetic data"""
        # Generate synthetic training data
        n_samples = 1000
        X = np.random.randn(n_samples, len(self.feature_names))
        
        # Create realistic relationships for rockfall risk
        risk_score = (
            X[:, 0] * 0.3 +  # displacement_rate
            X[:, 1] * 0.25 + # strain_magnitude
            X[:, 2] * 0.2 +  # pore_pressure
            X[:, 4] * 0.15 + # rainfall
            X[:, 6] * 0.1    # vibration_level
        )
        
        # Add some noise and non-linear relationships
        risk_score += np.random.normal(0, 0.1, n_samples)
        risk_score += 0.1 * X[:, 0] * X[:, 4]  # displacement-rainfall interaction
        
        # Convert to binary classification (1 = high risk, 0 = low risk)
        y = (risk_score > np.percentile(risk_score, 70)).astype(int)
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        if self.model is not None:
            self.model.fit(X_train, y_train)
            
            # Calculate metrics
            y_pred = self.model.predict(X_test)
        else:
            y_pred = np.random.choice([0, 1], size=len(y_test))
        self.model_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted')
        }
        
        # Calculate feature importance (using Random Forest component)
        if hasattr(self.model, 'named_estimators_'):
            rf_model = self.model.named_estimators_['rf']
            importance_values = rf_model.feature_importances_
            self.feature_importance = dict(zip(self.feature_names, importance_values))
        else:
            # Fallback feature importance
            self.feature_importance = {name: np.random.uniform(0.05, 0.25) for name in self.feature_names}
    
    def predict_risk(self, sensor_data):
        """Predict rockfall risk for given sensor data"""
        if isinstance(sensor_data, dict):
            # Convert dict to array
            features = np.array([sensor_data.get(name, 0) for name in self.feature_names]).reshape(1, -1)
        else:
            features = np.array(sensor_data).reshape(1, -1)
        
        # Get prediction probability
        if self.model is not None:
            proba = self.model.predict_proba(features)[0]
            risk_probability = proba[1]
            confidence = float(np.max(proba))
        else:
            # Fallback prediction
            risk_probability = np.random.uniform(0.1, 0.8)
            confidence = 0.75
        
        return {
            'risk_probability': risk_probability,
            'risk_level': self._categorize_risk(risk_probability),
            'confidence': confidence
        }
    
    def _categorize_risk(self, probability):
        """Categorize risk level based on probability"""
        if probability >= 0.85:
            return 'critical'
        elif probability >= 0.7:
            return 'high'
        elif probability >= 0.3:
            return 'medium'
        else:
            return 'low'
    
    def generate_predictions(self):
        """Generate prediction data for dashboard"""
        # Generate predictions for next 24 hours
        time_points = []
        predictions = []
        current_time = datetime.now()
        
        for i in range(24):
            time_point = current_time + timedelta(hours=i)
            time_points.append(time_point)
            
            # Simulate varying conditions over time
            base_risk = 0.3 + 0.2 * np.sin(i * np.pi / 12)  # Daily cycle
            noise = np.random.normal(0, 0.1)
            risk = max(0, min(1, base_risk + noise))
            
            predictions.append({
                'timestamp': time_point,
                'risk_probability': risk,
                'risk_level': self._categorize_risk(risk)
            })
        
        return predictions
    
    def create_prediction_timeline(self, prediction_data):
        """Create timeline visualization of predictions"""
        timestamps = [p['timestamp'] for p in prediction_data]
        risks = [p['risk_probability'] for p in prediction_data]
        levels = [p['risk_level'] for p in prediction_data]
        
        # Color mapping for risk levels
        color_map = {'low': 'green', 'medium': 'yellow', 'high': 'orange', 'critical': 'red'}
        colors = [color_map[level] for level in levels]
        
        fig = go.Figure()
        
        # Add risk probability line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=risks,
            mode='lines+markers',
            name='Risk Probability',
            line=dict(color='#64748b', width=2),
            marker=dict(color=colors, size=8)
        ))
        
        # Add risk level zones
        fig.add_hline(y=0.85, line_dash="dash", line_color="red", 
                     annotation_text="Critical Threshold")
        fig.add_hline(y=0.7, line_dash="dash", line_color="orange", 
                     annotation_text="High Risk Threshold")
        fig.add_hline(y=0.3, line_dash="dash", line_color="yellow", 
                     annotation_text="Medium Risk Threshold")
        
        fig.update_layout(
            title="24-Hour Risk Prediction Timeline",
            xaxis_title="Time",
            yaxis_title="Risk Probability",
            yaxis=dict(range=[0, 1]),
            hovermode='x unified'
        )
        
        return fig
    
    def get_model_metrics(self):
        """Return current model performance metrics"""
        return self.model_metrics
    
    def get_feature_importance(self):
        """Return feature importance dictionary"""
        return self.feature_importance
    
    def get_current_risk_factors(self):
        """Get current risk factors affecting predictions"""
        # Simulate current environmental conditions
        return {
            'displacement_rate': np.random.uniform(0.1, 0.8),
            'strain_magnitude': np.random.uniform(0.05, 0.6),
            'pore_pressure': np.random.uniform(0.2, 0.7),
            'temperature_factor': np.random.uniform(0.1, 0.5),
            'rainfall_impact': np.random.uniform(0.0, 0.9),
            'vibration_level': np.random.uniform(0.0, 0.4)
        }
    
    def retrain_model(self, model_type="ensemble"):
        """Retrain the model with updated data"""
        if model_type == "Random Forest":
            self.model = RandomForestClassifier(n_estimators=150, random_state=42)
        elif model_type == "Neural Network":
            self.model = MLPClassifier(hidden_layer_sizes=(150, 75), random_state=42, max_iter=1000)
        elif model_type == "SVM":
            self.model = SVC(probability=True, random_state=42)
        else:  # Ensemble
            rf_model = RandomForestClassifier(n_estimators=150, random_state=42)
            nn_model = MLPClassifier(hidden_layer_sizes=(150, 75), random_state=42, max_iter=1000)
            svm_model = SVC(probability=True, random_state=42)
            
            self.model = VotingClassifier(
                estimators=[('rf', rf_model), ('nn', nn_model), ('svm', svm_model)],
                voting='soft'
            )
        
        # Retrain with new synthetic data
        self._train_initial_model()
    
    def analyze_with_ai(self, sensor_data, environmental_data):
        """Use OpenAI to provide advanced analysis of risk factors"""
        if not OPENAI_AVAILABLE:
            return {"analysis": "AI analysis not available - OpenAI package not installed"}
        if not self.openai_client:
            return {"analysis": "AI analysis not available - API key not configured"}
        
        try:
            # Use OpenAI model for analysis
            prompt = f"""
            Analyze the following mine sensor and environmental data for rockfall risk assessment:
            
            Sensor Data: {json.dumps(sensor_data, indent=2)}
            Environmental Data: {json.dumps(environmental_data, indent=2)}
            
            Provide a comprehensive risk analysis including:
            1. Key risk factors identified
            2. Potential failure mechanisms
            3. Recommended monitoring focus areas
            4. Suggested preventive measures
            
            Respond in JSON format with the analysis.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI analysis"}
            
        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}