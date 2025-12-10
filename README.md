# IntruViz: Honeypot with Visualization Dashboard for Intrusion Analysis

## **CRITICAL SECURITY WARNING** 
**THIS HONEYPOT IS FOR LAB/EDUCATIONAL USE ONLY**
- **DO NOT EXPOSE TO PUBLIC INTERNET** without proper isolation
- **DO NOT USE IN PRODUCTION ENVIRONMENTS** 
- **PII HANDLING**: All attacker inputs are logged - ensure compliance with data protection laws
- **LEGAL COMPLIANCE**: Ensure honeypot deployment complies with local cybersecurity laws

---

## 📋 Project Overview

This is a comprehensive honeypot system with real-time analytics, designed for cybersecurity education and research. The project consists of multiple integrated modules:

### **Core Honeypot System:**
- **Flask Web Honeypot**: Fake login pages and admin panels
- **Attack Logging**: Dual JSONL + SQLite storage system  
- **Attack Simulation**: Automated testing with various attack patterns

### **Operator Dashboard & Real-time Analytics:** 
- **Real-time Monitoring**: WebSocket-based live event streaming
- **Interactive Dashboard**: Charts, maps, and analytics
- **Attack Visualization**: Geographic attack origin mapping
- **Data Export**: CSV export with filtering capabilities
- **Secure Access**: Password-protected operator interface

---

## 🚀 Quick Start

### **1. Installation**
```bash
# Clone and navigate to project
cd honeypot-project

# Install dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### **2. Basic Honeypot (Modules A-C)**
```bash
# Start basic honeypot
python simple_honeypot.py

# - Honeypot: http://localhost:8080/login
# - Admin panel: http://localhost:8080/admin/ (password: admin123)
```

### **3. Operator Dashboard (Module D)**
```bash
# Start operator dashboard (separate terminal)
python backend/operator_app.py

# Access dashboard:
# - URL: http://127.0.0.1:8090/operator
# - Password: honeypot2024!
```

### **4. Attack Simulation & Testing**
```bash
# Run automated attacks (separate terminal)
python test_attacks.py

# Or run comprehensive attack suite
python run_attacks.py


## 🛠️ Operator Dashboard

### **Features**
- **🔴 Live Events Feed**: Real-time attack monitoring with auto-scroll
- **📊 Analytics Charts**: Timeline, top countries, top IPs, attack type distribution
- **🗺️ Attack Origins Map**: Interactive world map showing geolocated attackers
- **🔍 Event Details**: Deep-dive into individual attack events with raw data
- **🎛️ Filtering & Search **: Filter by IP, country, time range, attack type
- **📥 Data Export**: Export filtered results to CSV
- **🔐 Secure Access**: Password-protected with session management

### **API Endpoints**
```
# Authentication
POST /operator/login       # Authenticate with operator password
GET  /operator/logout      # Clear session and logout

# Dashboard Views  
GET  /operator             # Main dashboard interface
GET  /operator/event/<id>  # Detailed event view

# Data API
GET  /api/events           # Paginated events with filtering
GET  /api/event/<id>       # Single event details
GET  /api/stats            # Dashboard statistics
GET  /api/map_points       # Geolocation data for map
GET  /api/export/csv       # Export events as CSV

# System
GET  /health               # Health check endpoint
```
### **Real-time WebSocket**
```
# WebSocket namespace: /events
ws://127.0.0.1:8090/socket.io/?EIO=4&transport=websocket

# Events:
- event.new     # New attack detected
- event.updated # Event enrichment completed
```
### **Configuration**
```python
# honeypot/config.py
OPERATOR_PASSWORD = 'honeypot2024!'      # Dashboard password
OPERATOR_BIND = '127.0.0.1'             # Bind address  
OPERATOR_PORT = 8090                     # Dashboard port
OPERATOR_SESSION_SECRET = 'secret-key'   # Session encryption
```

## 🧪 Testing

### **Run API Tests**
```bash
# Test operator API endpoints
python -m pytest tests/test_operator_api.py -v

# Test real-time functionality  
python -m pytest tests/test_realtime.py -v

# Run all tests
python -m pytest tests/ -v
```

### **Manual Testing**
```bash
# 1. Start honeypot
python simple_honeypot.py

# 2. Start dashboard (new terminal)
python backend/operator_app.py

# 3. Generate test attacks (new terminal) 
python test_attacks.py

# 4. View live events in dashboard at:
# http://127.0.0.1:8090/operator
```

## 🛡️ Security Best Practices

### **Deployment Security**
- **Network Isolation**: Deploy in isolated network segments
- **Access Control**: Restrict dashboard access to authorized IPs only
- **HTTPS**: Use HTTPS in production with proper SSL certificates
- **Strong Passwords**: Change default operator password immediately
- **Monitoring**: Monitor honeypot logs for legitimate traffic accidentally captured

### **Data Protection**
- **PII Handling**: Implement data retention policies for logged data
- **Anonymization**: Consider IP address anonymization for long-term storage
- **Access Logs**: Log all dashboard access attempts
- **Backup Security**: Secure database backups with encryption

### **Legal Compliance**
- **Disclosure**: Properly disclose honeypot presence where legally required
- **Data Laws**: Comply with GDPR, CCPA, and other data protection regulations
- **Evidence Chain**: Maintain proper chain of custody for research data
- **Research Ethics**: Follow institutional research ethics guidelines

---
### **Project Structure**
```
honeypot-project/
├── honeypot/                 # Core honeypot modules
│   ├── config.py            # Configuration settings
│   ├── storage.py           # Database operations  
│   ├── logger.py            # Event logging
│   └── data/                # SQLite DB and logs
├── backend/                 # Operator dashboard backend
│   ├── operator_app.py      # Flask app
│   ├── socket_bridge.py     # WebSocket handling
│   └── api_tools.py         # API utilities
├── frontend/                # Dashboard frontend
│   ├── operator_templates/  # HTML templates
│   └── operator_static/     # CSS/JS assets
├── tests/                   # Test suites
├── simple_honeypot.py       # Standalone honeypot
└── requirements.txt         # Dependencies
```
---

## 📚 Additional Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Flask-SocketIO Guide**: https://flask-socketio.readthedocs.io/
- **Chart.js Documentation**: https://www.chartjs.org/docs/
- **Leaflet Maps Guide**: https://leafletjs.com/examples/
- **Cybersecurity Research**: NIST Cybersecurity Framework
- **Honeypot Best Practices**: SANS Institute Guidelines

---

## 📞 Support & Issues

For educational use and research questions:
1. Check the test suites for implementation examples
2. Review configuration options in `honeypot/config.py`
3. Examine API endpoints in `backend/operator_app.py`
4. Test with provided sample data and scripts

**Remember: This is educational software - use responsibly and legally!**

---

*Last Updated: October 2024 - Module D (Real-time Analytics) v1.0*
