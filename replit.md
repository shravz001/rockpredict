# AI-Based Rockfall Prediction & Alert System

## Overview

This is a comprehensive AI-powered rockfall prediction and alert system designed for open-pit mines. The system combines machine learning models with real-time sensor data, environmental monitoring, and multi-channel communication systems to predict rockfall risks and provide early warnings to ensure mine safety. The application features a web-based dashboard built with Streamlit, 3D mine visualization, historical analysis capabilities, and robust communication systems including LoRaWAN and radio backup for reliable operation even in remote locations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Frontend Architecture:**
- Streamlit-based web application serving as the main dashboard
- Real-time data visualization using Plotly for 3D mine views, risk heatmaps, and sensor monitoring
- Responsive dashboard with navigation sidebar for different system components
- Mobile field application interface for on-site personnel

**Backend Architecture:**
- Modular Python architecture with separate packages for different functionalities
- Machine learning ensemble model combining Random Forest, Neural Networks, and SVM for rockfall prediction
- Synthetic data generator for testing and simulation when real sensors are unavailable
- Real-time data processing pipeline with configurable update intervals
- Historical analysis engine with trend detection and correlation analysis

**Data Storage:**
- SQLAlchemy ORM with support for multiple database backends
- VS Code-friendly database configuration with local SQLite default and PostgreSQL support
- Comprehensive database schema including mine sites, sensors, readings, alerts, and environmental data
- Data ingestion system supporting multiple IoT protocols
- Automatic data retention and cleanup policies
- Local database files stored in ./data/ directory for VS Code development

**Communication Systems:**
- LoRaWAN simulation and management for low-power, long-range sensor communication
- Radio communication backup systems for redundancy
- Multi-channel alert system supporting SMS (Twilio), email (SendGrid), and audio/visual alerts
- MQTT and HTTP API support for real-time data streaming

**AI/ML Components:**
- Ensemble machine learning model with continuous learning capabilities
- Feature engineering for geological and environmental parameters
- Risk probability calculation with configurable thresholds
- Pattern recognition for historical data analysis
- Optional OpenAI integration for advanced analysis and insights

**Hardware Integration:**
- IoT sensor management system supporting multiple communication protocols
- Physical siren and emergency broadcast system integration
- Hardware status monitoring and maintenance scheduling
- Battery and signal strength monitoring for remote sensors

**Mobile and Field Support:**
- Offline-capable field application for inspectors
- Emergency communication protocols
- Field report generation and photo documentation
- GPS-based location tracking for incidents and inspections

## External Dependencies

**Machine Learning Libraries:**
- scikit-learn for ensemble models and data preprocessing
- numpy and pandas for numerical computations and data manipulation
- scipy for statistical analysis

**Visualization and UI:**
- Streamlit for web application framework
- Plotly for interactive 3D visualizations and charts
- plotly.express for statistical plotting

**Communication Services:**
- Twilio REST API for SMS notifications
- SendGrid API for email alerts
- MQTT protocol support via paho-mqtt
- HTTP APIs for data ingestion

**Database:**
- SQLAlchemy ORM for database abstraction
- Default SQLite configuration for VS Code development (./data/rockfall_prediction.db)
- Optional PostgreSQL support via environment variables
- Support for local and remote database configurations
- Automatic schema migration and table creation
- Environment-based configuration with .env.example provided

**IoT and Hardware:**
- LoRaWAN protocol simulation and management
- Modbus support for industrial sensors
- ZigBee and WiFi sensor protocols
- Cellular communication backup

**Optional Integrations:**
- OpenAI API for advanced AI analysis and natural language insights
- Computer vision libraries (OpenCV) for drone imagery analysis
- Satellite communication systems for remote area connectivity

**Development and Deployment:**
- JSON-based configuration management
- Comprehensive logging system
- Modular architecture supporting easy extension and customization
- Environment variable configuration for sensitive credentials