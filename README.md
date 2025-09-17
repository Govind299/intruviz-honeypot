# Web Application Honeypot

A production-quality Flask-based honeypot that simulates a realistic login page to capture and analyze attacker interactions in a controlled lab environment.

## ⚠️ SECURITY WARNING

**THIS HONEYPOT IS FOR LAB/EDUCATIONAL USE ONLY!**

- Do not expose to the public internet without proper isolation
- Use only in controlled environments (VM, isolated VLAN, or containerized)
- Monitor all logged interactions carefully
- This tool captures sensitive data including passwords - handle responsibly

## 🎯 Features

- **Realistic Login Interface**: Professional-looking corporate login page
- **Comprehensive Logging**: Thread-safe JSONL logging with detailed event capture
- **Attack Detection**: Captures SQL injection, XSS, credential stuffing attempts
- **Client-Side Analytics**: JavaScript-based interaction tracking and behavioral analysis
- **Rate Limiting**: Built-in protection against log spam and resource exhaustion
- **Security Hardening**: Input sanitization and proper error handling
- **Easy Deployment**: Simple setup with Docker support

## 📁 Project Structure

```
honeypot/
├── config.py           # Configuration settings
├── logger.py           # Thread-safe JSONL logging system
├── webapp.py           # Main Flask application
├── templates/
│   └── login.html      # Fake login page template
├── static/
│   ├── css/
│   │   └── style.css   # Professional styling
│   └── js/
│       └── honeypot.js # Client-side event capture
├── data/               # Log files (created automatically)
└── tests/
    └── test_simulate.py # Automated testing suite
requirements.txt        # Python dependencies
run.sh                 # Quick start script
README.md              # This file
Dockerfile             # Container deployment
docker-compose.yml     # Container orchestration
```

## 🚀 Quick Start

### Method 1: Local Python Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate     # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the honeypot**:
   ```bash
   # Using the run script
   .\run.sh                  # Windows
   # ./run.sh                # Linux/Mac
   
   # Or directly
   python -m honeypot.webapp
   ```

4. **Access the honeypot**:
   - Open browser to `http://127.0.0.1:8080/login`
   - Try submitting test credentials
   - Monitor logs in `honeypot/data/web_honeypot.jsonl`

### Method 2: Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Access the honeypot**:
   - Browser: `http://localhost:8080/login`
   - Logs: `./data/web_honeypot.jsonl` (mounted volume)

3. **Stop the honeypot**:
   ```bash
   docker-compose down
   ```

## 🧪 Testing and Simulation

### Automated Testing

Run the comprehensive test suite:

```bash
# Test local instance
python -m honeypot.tests.test_simulate

# Test remote instance
python -m honeypot.tests.test_simulate --host 192.168.1.100 --port 8080
```

### Manual Testing with cURL

#### Basic GET request
```bash
curl -i http://127.0.0.1:8080/login
```

#### Simple login attempt
```bash
curl -X POST -d "username=admin&password=password123" http://127.0.0.1:8080/login
```

#### SQL Injection attempts
```bash
# Basic SQLi
curl -X POST -d "username=admin&password=admin' OR '1'='1" http://127.0.0.1:8080/login

# Union-based SQLi
curl -X POST -d "username=admin&password=1' UNION SELECT * FROM users --" http://127.0.0.1:8080/login

# Blind SQLi
curl -X POST -d "username=admin'; DROP TABLE users; --&password=test" http://127.0.0.1:8080/login
```

#### XSS attempts
```bash
curl -X POST -d "username=<script>alert('XSS')</script>&password=test" http://127.0.0.1:8080/login
curl -X POST -d "username=admin&password=<img src=x onerror=alert('XSS')>" http://127.0.0.1:8080/login
```

#### Tool simulation
```bash
# Simulate sqlmap
curl -X POST -H "User-Agent: sqlmap/1.6.12" \
     -d "username=admin&password=test' OR 1=1 --" \
     http://127.0.0.1:8080/login

# Simulate Burp Suite
curl -X POST -H "User-Agent: Mozilla/5.0 (compatible; BurpSuite)" \
     -d "username=admin&password={{7*7}}" \
     http://127.0.0.1:8080/login
```

### Testing with Security Tools

#### Nmap scan
```bash
nmap -sV -p 8080 127.0.0.1
```

#### Directory enumeration with dirb
```bash
dirb http://127.0.0.1:8080/
```

#### SQLMap testing
```bash
sqlmap -u "http://127.0.0.1:8080/login" --data "username=admin&password=test" --batch
```

## 📊 Log Analysis

### Log Format

Events are logged in newline-delimited JSON (JSONL) format with the following fields:

```json
{
  "id": "uuid-v4-string",
  "timestamp": "2025-01-15T10:30:45.123456Z",
  "client_ip": "192.168.1.100",
  "method": "POST",
  "endpoint": "/login",
  "full_path": "/login",
  "headers": {
    "User-Agent": "Mozilla/5.0...",
    "Content-Type": "application/x-www-form-urlencoded"
  },
  "query_params": {},
  "cookies": {},
  "form_data": {
    "username": "admin",
    "password": "admin' OR '1'='1"
  },
  "user_agent": "Mozilla/5.0...",
  "raw_body_preview": "username=admin&password=admin%27+OR+%271%27%3D%271",
  "action": "login_attempt",
  "username": "admin",
  "password": "admin' OR '1'='1",
  "credentials_captured": true
}
```

### Sample Log Entries

**Basic login attempt:**
```json
{"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "timestamp": "2025-01-15T10:30:45.123Z", "client_ip": "127.0.0.1", "method": "POST", "endpoint": "/login", "headers": {"User-Agent": "curl/7.68.0", "Content-Type": "application/x-www-form-urlencoded"}, "form_data": {"username": "admin", "password": "password123"}, "action": "login_attempt"}
```

**SQL injection attempt:**
```json
{"id": "b2c3d4e5-f6a7-8901-bcde-f23456789012", "timestamp": "2025-01-15T10:31:15.456Z", "client_ip": "127.0.0.1", "method": "POST", "endpoint": "/login", "headers": {"User-Agent": "sqlmap/1.6.12"}, "form_data": {"username": "admin", "password": "admin' OR '1'='1"}, "action": "login_attempt", "potential_sqli": true}
```

**Rate limiting triggered:**
```json
{"id": "c3d4e5f6-a789-0123-cdef-456789012345", "timestamp": "2025-01-15T10:32:00.789Z", "client_ip": "192.168.1.100", "method": "POST", "endpoint": "/login", "rate_limited": true, "action": "blocked"}
```

### Analyzing Logs

```bash
# View recent entries
tail -n 20 honeypot/data/web_honeypot.jsonl

# Count total interactions
wc -l honeypot/data/web_honeypot.jsonl

# Extract unique source IPs
grep -o '"client_ip":"[^"]*"' honeypot/data/web_honeypot.jsonl | sort | uniq -c

# Find SQL injection attempts
grep "OR.*=" honeypot/data/web_honeypot.jsonl

# Find XSS attempts
grep -i "script\|onerror\|onload" honeypot/data/web_honeypot.jsonl

# Extract user agents
jq -r '.user_agent' honeypot/data/web_honeypot.jsonl | sort | uniq -c | sort -nr
```

## ⚙️ Configuration

Edit `honeypot/config.py` to customize behavior:

```python
# Server settings
HOST = "0.0.0.0"      # Listen address
PORT = 8080           # Listen port

# Logging settings
LOG_PATH = "honeypot/data/web_honeypot.jsonl"
FORCE_FSYNC = True    # Force disk writes
MAX_LOG_LINE_BYTES = 1024

# Rate limiting
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW = 300    # Window in seconds

# Security
MAX_BODY_SIZE = 16 * 1024  # Max request size
DEBUG = False              # Never enable in production
```

## 🛡️ Security Considerations

### Deployment Security

1. **Network Isolation**: Deploy in isolated VLAN or VM
2. **Firewall Rules**: Restrict access to necessary ports only
3. **Monitoring**: Monitor honeypot host for compromise indicators
4. **Log Rotation**: Implement log rotation to prevent disk fill
5. **Access Control**: Restrict access to log files

### Legal and Ethical Considerations

1. **Authorization**: Only deploy with explicit authorization
2. **Jurisdiction**: Understand local laws regarding honeypots
3. **Data Handling**: Captured credentials may contain real passwords
4. **Incident Response**: Have procedures for handling real attacks
5. **Privacy**: Consider privacy implications of data capture

## 🔧 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using port 8080
netstat -an | findstr :8080    # Windows
# netstat -an | grep :8080     # Linux/Mac

# Change port in config.py or use environment variable
export HONEYPOT_PORT=8081
```

**Permission denied for log file:**
```bash
# Ensure directory exists and is writable
mkdir -p honeypot/data
chmod 755 honeypot/data
```

**High memory usage:**
```bash
# Check log file size
ls -lh honeypot/data/web_honeypot.jsonl

# Implement log rotation
logrotate /etc/logrotate.d/honeypot
```

### Debug Mode

For debugging (development only):
```python
# In config.py
DEBUG = True
```

**WARNING**: Never enable debug mode in production!

## 📈 Enhancement Ideas

### Immediate Improvements
- [ ] GeoIP enrichment for source location data
- [ ] Database storage option (SQLite/PostgreSQL)
- [ ] Web dashboard for real-time monitoring
- [ ] Email/Slack notifications for suspicious activity
- [ ] Custom response pages based on attack type

### Advanced Features
- [ ] Machine learning for attack classification
- [ ] Integration with threat intelligence feeds
- [ ] Distributed honeypot coordination
- [ ] Advanced behavioral analytics
- [ ] Automated response mechanisms

## 🤝 Contributing

This honeypot is designed for educational and research purposes. When contributing:

1. Maintain security-first approach
2. Document all changes thoroughly
3. Test in isolated environments only
4. Follow responsible disclosure for vulnerabilities

## 📄 License

Educational/Research use only. See legal considerations section.

---

**Remember**: This tool captures real attack data. Handle responsibly and in accordance with your organization's security policies and applicable laws.