"""
Advanced Deep Learning System for Drone Imagery Analysis
Implements computer vision models for crack detection, slope stability analysis,
and automated geological assessment using drone imagery
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import cv2
import requests
from database.database_manager import RockfallDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrackDetection:
    """Detected crack information"""
    crack_id: str
    coordinates: List[Tuple[int, int]]  # Pixel coordinates
    length: float  # meters
    width: float   # millimeters
    severity: str  # low, medium, high, critical
    confidence: float
    crack_type: str  # surface, deep, stress, expansion

@dataclass
class DroneImageAnalysis:
    """Complete drone image analysis results"""
    image_id: str
    timestamp: datetime
    flight_id: str
    gps_coordinates: Dict[str, float]
    altitude: float
    
    # Image properties
    image_path: str
    resolution: Tuple[int, int]
    image_quality: float
    
    # Analysis results
    cracks_detected: List[CrackDetection]
    slope_stability_score: float
    erosion_indicators: List[Dict[str, Any]]
    vegetation_coverage: float
    geological_features: List[Dict[str, Any]]
    
    # Change detection (compared to previous images)
    changes_detected: List[Dict[str, Any]]
    change_severity: str
    
    # Risk assessment
    overall_risk_score: float
    risk_factors: List[str]
    recommendations: List[str]

class DroneImageProcessor:
    """Advanced drone image processing with deep learning"""
    
    def __init__(self):
        self.db_manager = RockfallDatabaseManager()
        
        # Model configurations (in production, these would be actual AI models)
        self.crack_detection_model = self._initialize_crack_detection_model()
        self.stability_analysis_model = self._initialize_stability_model()
        self.change_detection_model = self._initialize_change_detection_model()
        
        # Image processing parameters
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif']
        self.min_resolution = (1920, 1080)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    def _initialize_crack_detection_model(self) -> Dict[str, Any]:
        """Initialize crack detection model (simulated)"""
        # In production, this would load a trained CNN model (e.g., U-Net, DeepCrack)
        return {
            'model_type': 'DeepCrack_CNN',
            'version': '2.1.0',
            'input_size': (512, 512, 3),
            'confidence_threshold': 0.7,
            'min_crack_length': 10,  # pixels
            'trained_on': 'mining_dataset_v3'
        }
    
    def _initialize_stability_model(self) -> Dict[str, Any]:
        """Initialize slope stability analysis model (simulated)"""
        # In production, this would be a specialized geological analysis model
        return {
            'model_type': 'SlopeNet_ResNet50',
            'version': '1.8.2',
            'input_size': (1024, 1024, 3),
            'features': ['slope_angle', 'surface_texture', 'vegetation', 'moisture'],
            'stability_classes': ['stable', 'monitor', 'caution', 'unstable'],
            'trained_on': 'geological_survey_dataset'
        }
    
    def _initialize_change_detection_model(self) -> Dict[str, Any]:
        """Initialize change detection model (simulated)"""
        # In production, this would use temporal CNN or Siamese networks
        return {
            'model_type': 'ChangeNet_Siamese',
            'version': '1.5.1',
            'time_sensitivity': 30,  # days
            'change_threshold': 0.15,
            'min_change_area': 100,  # square pixels
            'change_types': ['erosion', 'rockfall', 'vegetation_change', 'surface_crack']
        }
    
    def process_drone_image(self, image_path: str, flight_id: str, 
                          gps_coords: Dict[str, float], altitude: float) -> DroneImageAnalysis:
        """Process a single drone image with complete analysis"""
        try:
            # Validate and load image
            if not self._validate_image(image_path):
                raise ValueError(f"Invalid image: {image_path}")
            
            # Generate unique image ID
            image_id = f"img_{flight_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Load image for processing
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            height, width = image.shape[:2]
            
            # Perform crack detection
            logger.info(f"Running crack detection on {image_id}")
            cracks = self._detect_cracks(image, image_id)
            
            # Perform slope stability analysis
            logger.info(f"Analyzing slope stability for {image_id}")
            stability_score = self._analyze_slope_stability(image)
            
            # Detect erosion indicators
            logger.info(f"Detecting erosion indicators for {image_id}")
            erosion_indicators = self._detect_erosion(image)
            
            # Analyze vegetation coverage
            vegetation_coverage = self._analyze_vegetation(image)
            
            # Identify geological features
            geological_features = self._identify_geological_features(image)
            
            # Perform change detection (if previous images exist)
            changes_detected, change_severity = self._detect_changes(image, gps_coords, flight_id)
            
            # Calculate overall risk assessment
            risk_score, risk_factors, recommendations = self._assess_overall_risk(
                cracks, stability_score, erosion_indicators, changes_detected
            )
            
            # Create analysis result
            analysis = DroneImageAnalysis(
                image_id=image_id,
                timestamp=datetime.now(),
                flight_id=flight_id,
                gps_coordinates=gps_coords,
                altitude=altitude,
                image_path=image_path,
                resolution=(width, height),
                image_quality=self._assess_image_quality(image),
                cracks_detected=cracks,
                slope_stability_score=stability_score,
                erosion_indicators=erosion_indicators,
                vegetation_coverage=vegetation_coverage,
                geological_features=geological_features,
                changes_detected=changes_detected,
                change_severity=change_severity,
                overall_risk_score=risk_score,
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
            # Store results in database
            self._store_analysis_results(analysis)
            
            logger.info(f"Completed analysis for {image_id} - Risk Score: {risk_score:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing drone image {image_path}: {e}")
            raise
    
    def _validate_image(self, image_path: str) -> bool:
        """Validate image file"""
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False
        
        # Check file extension
        _, ext = os.path.splitext(image_path)
        if ext.lower() not in self.supported_formats:
            logger.error(f"Unsupported image format: {ext}")
            return False
        
        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > self.max_file_size:
            logger.error(f"Image file too large: {file_size} bytes")
            return False
        
        return True
    
    def _detect_cracks(self, image: np.ndarray, image_id: str) -> List[CrackDetection]:
        """Detect cracks using deep learning model (simulated)"""
        cracks = []
        
        try:
            # Simulate advanced crack detection algorithm
            # In production, this would use a trained CNN model
            
            # Convert to grayscale for edge detection simulation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Simulate finding crack-like features
            # Using Canny edge detection as a simplified example
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours that could represent cracks
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            crack_count = 0
            for i, contour in enumerate(contours):
                # Filter contours by area and aspect ratio to identify crack-like features
                area = cv2.contourArea(contour)
                if area < 50:  # Too small
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = max(w, h) / min(w, h)
                
                # Cracks typically have high aspect ratio (long and thin)
                if aspect_ratio < 3:
                    continue
                
                # Simulate crack properties
                crack_length = cv2.arcLength(contour, False) * 0.001 * (altitude / 100)  # Convert to meters
                crack_width = min(w, h) * 0.1  # Simulate width in mm
                
                # Determine severity based on length and width
                if crack_length > 5.0 or crack_width > 10.0:
                    severity = "critical"
                elif crack_length > 2.0 or crack_width > 5.0:
                    severity = "high"
                elif crack_length > 1.0 or crack_width > 2.0:
                    severity = "medium"
                else:
                    severity = "low"
                
                # Simulate confidence score
                confidence = min(0.95, 0.6 + (area / 1000) * 0.3)
                
                # Create crack detection
                crack = CrackDetection(
                    crack_id=f"{image_id}_crack_{crack_count:03d}",
                    coordinates=[(int(x), int(y)) for x, y in contour.reshape(-1, 2)[:10]],  # First 10 points
                    length=crack_length,
                    width=crack_width,
                    severity=severity,
                    confidence=confidence,
                    crack_type=self._classify_crack_type(contour, gray)
                )
                
                cracks.append(crack)
                crack_count += 1
                
                # Limit number of detected cracks
                if crack_count >= 20:
                    break
            
            logger.info(f"Detected {len(cracks)} cracks in {image_id}")
            
        except Exception as e:
            logger.error(f"Error in crack detection: {e}")
        
        return cracks
    
    def _classify_crack_type(self, contour: np.ndarray, gray_image: np.ndarray) -> str:
        """Classify crack type based on shape and surrounding context"""
        # Simplified crack classification
        # In production, this would use advanced ML classification
        
        # Analyze contour properties
        perimeter = cv2.arcLength(contour, False)
        area = cv2.contourArea(contour)
        
        if area == 0:
            return "surface"
        
        compactness = (perimeter * perimeter) / area
        
        if compactness > 50:
            return "stress"
        elif compactness > 25:
            return "expansion"
        elif compactness > 15:
            return "deep"
        else:
            return "surface"
    
    def _analyze_slope_stability(self, image: np.ndarray) -> float:
        """Analyze slope stability using computer vision (simulated)"""
        try:
            # Simulate slope stability analysis
            # In production, this would use specialized geological AI models
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Analyze texture features (using standard deviation as proxy)
            texture_score = np.std(gray) / 255.0
            
            # Analyze edge density (proxy for surface roughness)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Analyze color distribution (proxy for geological composition)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            color_variance = np.std(hsv[:, :, 1]) / 255.0  # Saturation variance
            
            # Combine factors for stability score
            # Higher texture and edge density might indicate instability
            # This is a simplified example
            stability_score = max(0.0, min(1.0, 
                0.8 - (texture_score * 0.3) - (edge_density * 0.4) - (color_variance * 0.2)
            ))
            
            return stability_score
            
        except Exception as e:
            logger.error(f"Error in slope stability analysis: {e}")
            return 0.5  # Default moderate stability
    
    def _detect_erosion(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect erosion indicators (simulated)"""
        erosion_indicators = []
        
        try:
            # Simulate erosion detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Look for erosion patterns (simplified example)
            # In production, this would use trained models for erosion detection
            
            # Detect potential erosion channels using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
            erosion_mask = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            
            # Find contours in erosion mask
            contours, _ = cv2.findContours(erosion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours[:5]):  # Limit to 5 indicators
                area = cv2.contourArea(contour)
                if area < 100:  # Filter small areas
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # Simulate erosion severity
                erosion_area = area / (width * height)
                if erosion_area > 0.01:
                    severity = "high"
                elif erosion_area > 0.005:
                    severity = "medium"
                else:
                    severity = "low"
                
                erosion_indicators.append({
                    'erosion_id': f"erosion_{i:02d}",
                    'location': {'x': int(x + w/2), 'y': int(y + h/2)},
                    'area': float(area),
                    'severity': severity,
                    'type': 'gully' if h > w else 'sheet',
                    'confidence': min(0.9, 0.5 + (area / 1000) * 0.4)
                })
            
        except Exception as e:
            logger.error(f"Error in erosion detection: {e}")
        
        return erosion_indicators
    
    def _analyze_vegetation(self, image: np.ndarray) -> float:
        """Analyze vegetation coverage percentage"""
        try:
            # Convert to HSV for better vegetation detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define green color range for vegetation
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])
            
            # Create mask for green areas
            vegetation_mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Calculate vegetation coverage percentage
            total_pixels = vegetation_mask.size
            vegetation_pixels = np.sum(vegetation_mask > 0)
            vegetation_coverage = vegetation_pixels / total_pixels
            
            return vegetation_coverage
            
        except Exception as e:
            logger.error(f"Error in vegetation analysis: {e}")
            return 0.0
    
    def _identify_geological_features(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Identify geological features (simulated)"""
        features = []
        
        try:
            # Simulate geological feature identification
            # In production, this would use specialized geological AI models
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect rock formations using edge detection and clustering
            edges = cv2.Canny(gray, 100, 200)
            
            # Find large connected components that might represent rock formations
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            large_contours = [c for c in contours if cv2.contourArea(c) > 500]
            
            for i, contour in enumerate(large_contours[:10]):  # Limit to 10 features
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Classify feature type based on shape
                aspect_ratio = w / h
                if aspect_ratio > 2:
                    feature_type = "ledge"
                elif aspect_ratio < 0.5:
                    feature_type = "vertical_face"
                else:
                    feature_type = "boulder"
                
                features.append({
                    'feature_id': f"geo_{i:02d}",
                    'type': feature_type,
                    'location': {'x': int(x + w/2), 'y': int(y + h/2)},
                    'dimensions': {'width': int(w), 'height': int(h)},
                    'area': float(area),
                    'stability_concern': area > 2000  # Large features might be unstable
                })
            
        except Exception as e:
            logger.error(f"Error in geological feature identification: {e}")
        
        return features
    
    def _detect_changes(self, current_image: np.ndarray, gps_coords: Dict[str, float], 
                       flight_id: str) -> Tuple[List[Dict[str, Any]], str]:
        """Detect changes compared to previous images (simulated)"""
        changes = []
        severity = "none"
        
        try:
            # In production, this would compare with previous images from the same location
            # For simulation, we'll generate some sample changes
            
            height, width = current_image.shape[:2]
            
            # Simulate change detection results
            import random
            if random.random() < 0.3:  # 30% chance of detecting changes
                num_changes = random.randint(1, 3)
                
                for i in range(num_changes):
                    change_type = random.choice(['erosion', 'rockfall', 'vegetation_change', 'surface_crack'])
                    
                    x = random.randint(0, width - 100)
                    y = random.randint(0, height - 100)
                    size = random.randint(50, 200)
                    
                    change_severity = random.choice(['low', 'medium', 'high'])
                    
                    changes.append({
                        'change_id': f"change_{i:02d}",
                        'type': change_type,
                        'location': {'x': x, 'y': y},
                        'size': size,
                        'severity': change_severity,
                        'confidence': random.uniform(0.6, 0.95),
                        'time_detected': datetime.now().isoformat()
                    })
                
                # Determine overall severity
                severities = [c['severity'] for c in changes]
                if 'high' in severities:
                    severity = "high"
                elif 'medium' in severities:
                    severity = "medium"
                else:
                    severity = "low"
            
        except Exception as e:
            logger.error(f"Error in change detection: {e}")
        
        return changes, severity
    
    def _assess_overall_risk(self, cracks: List[CrackDetection], stability_score: float,
                           erosion_indicators: List[Dict[str, Any]], 
                           changes: List[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """Assess overall risk and provide recommendations"""
        risk_score = 0.0
        risk_factors = []
        recommendations = []
        
        try:
            # Base risk from slope stability
            risk_score += (1.0 - stability_score) * 0.3
            
            # Risk from cracks
            critical_cracks = [c for c in cracks if c.severity == "critical"]
            high_cracks = [c for c in cracks if c.severity == "high"]
            
            if critical_cracks:
                risk_score += 0.4
                risk_factors.append(f"{len(critical_cracks)} critical cracks detected")
                recommendations.append("Immediate inspection of critical crack areas required")
            
            if high_cracks:
                risk_score += 0.2
                risk_factors.append(f"{len(high_cracks)} high-severity cracks detected")
                recommendations.append("Schedule detailed crack monitoring")
            
            # Risk from erosion
            high_erosion = [e for e in erosion_indicators if e['severity'] == "high"]
            if high_erosion:
                risk_score += 0.2
                risk_factors.append("High erosion activity detected")
                recommendations.append("Implement erosion control measures")
            
            # Risk from changes
            high_changes = [c for c in changes if c['severity'] == "high"]
            if high_changes:
                risk_score += 0.3
                risk_factors.append("Significant changes detected since last inspection")
                recommendations.append("Immediate field investigation recommended")
            
            # Cap risk score at 1.0
            risk_score = min(1.0, risk_score)
            
            # Add general recommendations based on risk level
            if risk_score > 0.8:
                recommendations.append("Consider temporary area evacuation")
                recommendations.append("Increase monitoring frequency to hourly")
            elif risk_score > 0.6:
                recommendations.append("Deploy additional sensors in high-risk areas")
                recommendations.append("Daily visual inspections recommended")
            elif risk_score > 0.3:
                recommendations.append("Weekly drone surveillance recommended")
                recommendations.append("Monitor weather conditions closely")
            else:
                recommendations.append("Continue routine monitoring schedule")
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            risk_score = 0.5  # Default moderate risk
            recommendations = ["Error in analysis - manual inspection required"]
        
        return risk_score, risk_factors, recommendations
    
    def _assess_image_quality(self, image: np.ndarray) -> float:
        """Assess image quality for analysis reliability"""
        try:
            # Calculate image quality metrics
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness (mean intensity)
            brightness = np.mean(gray)
            
            # Contrast (standard deviation)
            contrast = np.std(gray)
            
            # Normalize and combine metrics
            sharpness_score = min(1.0, sharpness / 1000)  # Normalize to 0-1
            brightness_score = 1.0 - abs(brightness - 128) / 128  # Optimal around 128
            contrast_score = min(1.0, contrast / 64)  # Normalize to 0-1
            
            # Weighted average
            quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return 0.5  # Default moderate quality
    
    def _store_analysis_results(self, analysis: DroneImageAnalysis):
        """Store analysis results in database"""
        try:
            # Convert analysis to database format and store
            # This would use the DroneImagery table from the database schema
            
            # For now, just log the results
            logger.info(f"Storing analysis results for {analysis.image_id}")
            logger.info(f"Cracks detected: {len(analysis.cracks_detected)}")
            logger.info(f"Overall risk score: {analysis.overall_risk_score:.2f}")
            
            # In production, this would store in the database:
            # self.db_manager.store_drone_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
    
    def batch_process_flight_images(self, flight_directory: str, flight_id: str) -> List[DroneImageAnalysis]:
        """Process all images from a drone flight"""
        results = []
        
        try:
            if not os.path.exists(flight_directory):
                logger.error(f"Flight directory not found: {flight_directory}")
                return results
            
            # Find all image files
            image_files = []
            for ext in self.supported_formats:
                pattern = os.path.join(flight_directory, f"*{ext}")
                import glob
                image_files.extend(glob.glob(pattern))
            
            logger.info(f"Processing {len(image_files)} images from flight {flight_id}")
            
            for image_path in image_files:
                try:
                    # Extract GPS coordinates from filename or metadata
                    # In production, this would parse EXIF data
                    gps_coords = self._extract_gps_from_filename(image_path)
                    altitude = 100.0  # Default altitude
                    
                    # Process image
                    analysis = self.process_drone_image(image_path, flight_id, gps_coords, altitude)
                    results.append(analysis)
                    
                except Exception as e:
                    logger.error(f"Error processing image {image_path}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(results)} images from flight {flight_id}")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
        
        return results
    
    def _extract_gps_from_filename(self, image_path: str) -> Dict[str, float]:
        """Extract GPS coordinates from image filename (simulated)"""
        # In production, this would parse EXIF data or filename patterns
        # For simulation, return approximate coordinates
        return {
            'latitude': 39.7392 + (hash(image_path) % 1000) / 100000,
            'longitude': -104.9903 + (hash(image_path) % 1000) / 100000
        }

# Global drone processor instance
drone_processor = DroneImageProcessor()