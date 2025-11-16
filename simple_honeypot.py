#!/usr/bin/env python3
"""
Simple Module C Honeypot Startup
Starts the honeypot with basic Flask (no SocketIO)
"""

import sys
import os
import json
import uuid
import sqlite3
import requests
from datetime import datetime

# Add honeypot directory to Python path
honeypot_dir = os.path.join(os.path.dirname(__file__), 'honeypot')
sys.path.insert(0, honeypot_dir)

from flask import Flask, request, render_template, render_template_string, session, redirect, url_for

def get_ip_geolocation(ip_address):
    """
    Get geolocation data for an IP address using ipgeolocation.io API.
    For localhost IPs, gets your real public IP for accurate geolocation.
    """
    print(f"Geolocation requested for IP: {ip_address}")
    
    # MANUAL OVERRIDE: Only for local testing (127.0.0.1), real IPs get real geolocation
    MANUAL_LOCATION_OVERRIDE = True  # Set to False to use API geolocation for ALL IPs
    YOUR_ACTUAL_LOCATION = {
        'country': 'India',
        'region': 'Gujarat (Actual_Location)',
        'city': 'Nadiad (User_Location)',
        'latitude': 22.6939,   # Nadiad coordinates
        'longitude': 72.8618,
        'isp': 'Reliance Jio (Actual User Location)',
        'timezone': 'Asia/Kolkata'
    }
    
    # Handle local/private IPs - use manual override for testing
    if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith(('192.168.', '10.', '172.')):
        if MANUAL_LOCATION_OVERRIDE:
            print(f"Local IP detected ({ip_address}) - using manual location (Nadiad)")
            return YOUR_ACTUAL_LOCATION
        else:
            print(f"Local IP detected ({ip_address}), getting your real public IP for geolocation...")
            try:
                # Get the real public IP for better geolocation data
                public_ip_response = requests.get('https://api.ipify.org', timeout=5)
                if public_ip_response.status_code == 200:
                    real_ip = public_ip_response.text.strip()
                    print(f"Your real public IP: {real_ip}")
                    # Continue with the real IP instead of localhost
                    ip_address = real_ip
                else:
                    print(f"Could not get public IP, status: {public_ip_response.status_code}")
                    return {
                        'country': 'GetIP_Failed',
                        'region': 'GetIP_Failed',
                        'city': 'GetIP_Failed', 
                        'latitude': 0.0,
                        'longitude': 0.0,
                        'isp': 'GetIP_Failed'
                    }
            except Exception as e:
                print(f"Could not get public IP: {e}")
                return {
                    'country': 'GetIP_Error',
                    'region': 'GetIP_Error',
                    'city': 'GetIP_Error', 
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'isp': 'GetIP_Error'
                }
    
    print(f"🌍 Looking up REAL geolocation for IP: {ip_address} (from IP grabber API)")
    
    # Try multiple APIs for better accuracy
    IPGEOLOCATION_API_KEY = "6910ce5a4c184b44b39803b73fd72bf5"
    
    # Method 1: Try ipgeolocation.io (your premium API key)
    try:
        response = requests.get(
            f'https://api.ipgeolocation.io/ipgeo?apiKey={IPGEOLOCATION_API_KEY}&ip={ip_address}',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if not data.get('message'):  # No error message
                # Add accuracy indicator
                accuracy_note = "ISP_Location" if data.get('city') == 'Vadodara' else "Estimated"
                result = {
                    'country': data.get('country_name', 'Unknown'),
                    'region': data.get('state_prov', 'Unknown') + f" ({accuracy_note})",
                    'city': data.get('city', 'Unknown') + f" (ISP: {data.get('isp', 'Unknown')})",
                    'latitude': float(data.get('latitude', 0.0)),
                    'longitude': float(data.get('longitude', 0.0)),
                    'isp': data.get('isp', 'Unknown'),
                    'timezone': data.get('time_zone', {}).get('name', 'Unknown') if isinstance(data.get('time_zone'), dict) else data.get('time_zone', 'Unknown'),
                    'country_code': data.get('country_code2', 'XX'),
                    'continent': data.get('continent_name', 'Unknown'),
                    'organization': data.get('organization', 'Unknown')
                }
                print(f"PREMIUM Geolocation: {result['country']}, {result['region']}, {result['city']} (ISP: {result['isp']})")
                return result
        else:
            print(f"ipgeolocation.io API error: Status {response.status_code}")
    except Exception as e:
        print(f"ipgeolocation.io failed: {e}")

    # Try ip-api.com as fallback (free)
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,lat,lon,isp,timezone', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = {
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'latitude': data.get('lat', 0.0),
                    'longitude': data.get('lon', 0.0),
                    'isp': data.get('isp', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown')
                }
                print(f"Fallback Geolocation: {result['country']}, {result['region']}, {result['city']}")
                return result
    except Exception as e:
        print(f"ip-api.com failed: {e}")
    
    # Try ipapi.co as fallback
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                result = {
                    'country': data.get('country_name', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'latitude': data.get('latitude', 0.0),
                    'longitude': data.get('longitude', 0.0),
                    'isp': data.get('org', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown')
                }
                print(f"Geolocation found (backup): {result['country']}, {result['region']}, {result['city']}")
                return result
    except Exception as e:
        print(f"ipapi.co failed: {e}")
    
    # Fallback data
    print(f"Geolocation lookup failed for {ip_address}")
    return {
        'country': 'Unknown',
        'region': 'Unknown', 
        'city': 'Unknown',
        'latitude': 0.0,
        'longitude': 0.0,
        'isp': 'Unknown',
        'timezone': 'Unknown'
    }

def create_simple_honeypot():
    """Create a simple honeypot without complex dependencies"""
    
    app = Flask(__name__, 
                template_folder=os.path.join(honeypot_dir, 'templates'),
                static_folder=os.path.join(honeypot_dir, 'static'))
    app.secret_key = 'honeypot-secret-key-2025'
    
    @app.route('/')
    def home():
        print(f"Root access from {request.remote_addr}")
        return redirect('/login')
    
    @app.route('/login', methods=['GET', 'POST'])
    @app.route('/login/', methods=['GET', 'POST'])
    def login():
        print(f"Login page accessed via {request.method} from {request.remote_addr}")
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            
            # Detect attack type based on input patterns
            attack_type = 'login_attempt'  # Default
            
            # SQL Injection patterns
            sql_patterns = ['SELECT', 'UNION', 'DROP', 'INSERT', 'UPDATE', 'DELETE', '--', ';--', 
                          'OR 1=1', "' OR '1'='1", '" OR "1"="1', 'OR 1=1--', 'EXEC', 'EXECUTE',
                          'xp_', 'sp_', 'INFORMATION_SCHEMA', 'WAITFOR DELAY']
            
            # XSS patterns
            xss_patterns = ['<script>', '</script>', 'javascript:', 'onerror=', 'onload=', 
                          '<img', '<iframe', 'alert(', 'eval(', 'document.cookie']
            
            # Command injection patterns
            cmd_patterns = ['&&', '||', ';', '|', '`', '$(', '${', '../', '..\\']
            
            # LDAP injection patterns
            ldap_patterns = ['*)(', ')(cn=', ')(uid=', ')(mail=']
            
            # Check username and password for attack patterns
            combined_input = (username + password).upper()
            username_lower = username.lower()
            password_lower = password.lower()
            
            # Detect SQL Injection
            if any(pattern.upper() in combined_input for pattern in sql_patterns):
                attack_type = 'sql_injection'
            # Detect XSS
            elif any(pattern.lower() in username_lower or pattern.lower() in password_lower for pattern in xss_patterns):
                attack_type = 'xss'
            # Detect Command Injection
            elif any(pattern in username or pattern in password for pattern in cmd_patterns):
                attack_type = 'command_injection'
            # Detect LDAP Injection
            elif any(pattern in username or pattern in password for pattern in ldap_patterns):
                attack_type = 'ldap_injection'
            # Check for admin unlock attempt
            elif password == 'admin123':
                attack_type = 'admin_unlock'
            # Check for brute force (common passwords)
            elif password in ['123456', 'password', 'admin', 'root', '12345678', 'qwerty', 'abc123']:
                attack_type = 'brute_force'
            
            # Enhanced logging with geolocation attempt
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'ip_address': request.remote_addr,
                'username': username,
                'password': password,
                'user_agent': request.headers.get('User-Agent', ''),
                'method': 'POST',
                'path': '/login',
                'country': 'Unknown',  # Would be filled by geolocation
                'region': 'Unknown',
                'city': 'Unknown',
                'attack_type': attack_type
            }
            
            # Enhanced geolocation lookup
            geo_data = get_ip_geolocation(request.remote_addr)
            log_entry.update({
                'country': geo_data.get('country', 'Unknown'),
                'region': geo_data.get('region', 'Unknown'), 
                'city': geo_data.get('city', 'Unknown'),
                'isp': geo_data.get('isp', 'Unknown'),
                'latitude': geo_data.get('latitude', 0.0),
                'longitude': geo_data.get('longitude', 0.0)
            })
            
            # Save to both JSON log file AND SQLite database
            log_file = os.path.join(honeypot_dir, 'data', 'web_honeypot.jsonl')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
                    f.flush()  # Force write to disk
                print(f"Log written to: {log_file}")
            except Exception as e:
                print(f"Log write error: {e}")
            
            # Save to SQLite database
            import sqlite3
            import uuid
            db_path = os.path.join(honeypot_dir, 'data', 'events.db')
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Insert into events table
                cursor.execute("""
                    INSERT INTO events (
                        id, timestamp, client_ip, method, endpoint, 
                        headers, form_data, user_agent, raw_json,
                        country, region, city, latitude, longitude, isp, enriched, attack_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    log_entry['timestamp'],
                    log_entry['ip_address'], 
                    'POST',
                    '/login',
                    json.dumps(dict(request.headers)),
                    json.dumps({'username': username, 'password': password}),
                    log_entry['user_agent'],
                    json.dumps(log_entry),
                    log_entry['country'],
                    log_entry['region'],
                    log_entry['city'],
                    log_entry.get('latitude', 0.0),
                    log_entry.get('longitude', 0.0),
                    log_entry.get('isp', 'Unknown'),
                    1,  # enriched = true
                    log_entry['attack_type']
                ))
                
                conn.commit()
                conn.close()
                print(f"SAVED TO DATABASE: {username}:{password}")
                
            except Exception as e:
                print(f"Database error: {e}")
            
            print(f"ATTACK CAPTURED: {username}:{password} from {request.remote_addr}")
            
            # Check for admin unlock
            if password == 'admin123':
                session['admin_authenticated'] = True
                print(f"ADMIN PANEL UNLOCKED by {request.remote_addr}")
                return redirect('/admin/')
            
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 50px; }
                    .error { max-width: 400px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; border-left: 4px solid #dc3545; }
                    h2 { color: #dc3545; margin-top: 0; }
                    .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin-top: 15px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Authentication Failed</h2>
                    <p>Invalid username or password.</p>
                    <a href="/login" class="btn">Try Again</a>
                </div>
            </body>
            </html>
            ''')
        
        # Serve login page
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure System Login</title>
            <meta charset="utf-8">
            <style>
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0; 
                    padding: 50px; 
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .login-container { 
                    max-width: 420px; 
                    width: 100%;
                    background: white; 
                    padding: 40px; 
                    border-radius: 12px; 
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                }
                .logo { text-align: center; margin-bottom: 30px; }
                .logo h1 { color: #2c3e50; margin: 0; font-size: 28px; }
                .logo p { color: #7f8c8d; margin: 5px 0 0 0; }
                .form-group { margin-bottom: 25px; }
                label { 
                    display: block; 
                    margin-bottom: 8px; 
                    color: #555; 
                    font-weight: 500;
                }
                input[type="text"], input[type="password"] { 
                    width: 100%; 
                    padding: 14px; 
                    border: 2px solid #e9ecef; 
                    border-radius: 6px; 
                    box-sizing: border-box;
                    font-size: 16px;
                    transition: border-color 0.3s ease;
                }
                input[type="text"]:focus, input[type="password"]:focus {
                    outline: none;
                    border-color: #667eea;
                }
                .btn { 
                    width: 100%; 
                    padding: 14px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    cursor: pointer; 
                    font-size: 16px;
                    font-weight: 500;
                    transition: transform 0.2s ease;
                }
                .btn:hover { 
                    transform: translateY(-2px);
                }
                .security-notice {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #6c757d;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">
                    <h1>SecureSystem</h1>
                    <p>Administrator Portal</p>
                </div>
                <form method="post">
                    <div class="form-group">
                        <label>Username:</label>
                        <input type="text" name="username" placeholder="Enter your username" required>
                    </div>
                    <div class="form-group">
                        <label>Password:</label>
                        <input type="password" name="password" placeholder="Enter your password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="security-notice">
                    This is a secure system. All access attempts are logged.
                </div>
            </div>
        </body>
        </html>
        ''')
    
    @app.route('/admin/')
    def admin_panel():
        if not session.get('admin_authenticated'):
            return redirect('/login')
        
        print(f"ADMIN PANEL ACCESSED by {request.remote_addr}")
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard - SecureSystem</title>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    background: #f8f9fa;
                    color: #333;
                }
                .header { 
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white; 
                    padding: 20px 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header h1 { font-size: 24px; margin-bottom: 5px; }
                .header p { opacity: 0.9; }
                .container { padding: 30px; max-width: 1200px; margin: 0 auto; }
                .stats-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 30px; 
                }
                .stat-card { 
                    background: white; 
                    padding: 25px; 
                    border-radius: 12px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .stat-number { font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 5px; }
                .stat-label { color: #6c757d; font-size: 14px; }
                .panel-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                }
                .panel { 
                    background: white; 
                    border-radius: 12px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                .panel-header { 
                    background: #667eea; 
                    color: white; 
                    padding: 20px; 
                    font-weight: 500;
                }
                .panel-content { padding: 25px; }
                .btn { 
                    padding: 12px 20px; 
                    background: #667eea; 
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    cursor: pointer; 
                    margin: 5px; 
                    font-size: 14px;
                    transition: background 0.3s ease;
                }
                .btn:hover { background: #5a67d8; }
                .btn.secondary { background: #6c757d; }
                .btn.danger { background: #dc3545; }
                .terminal { 
                    background: #1a1a1a; 
                    color: #00ff00; 
                    padding: 20px; 
                    font-family: 'Courier New', monospace; 
                    border-radius: 6px; 
                    font-size: 14px;
                    line-height: 1.4;
                }
                .user-list { list-style: none; }
                .user-list li { 
                    padding: 10px; 
                    border-bottom: 1px solid #eee; 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                }
                .user-status { 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 12px; 
                    background: #28a745; 
                    color: white;
                }
                .logout { 
                    position: absolute; 
                    top: 20px; 
                    right: 30px; 
                    background: #dc3545; 
                    color: white; 
                    padding: 8px 16px; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ Administrator Dashboard</h1>
                <p>Welcome to the SecureSystem Management Portal</p>
                <a href="/logout" class="logout">Logout</a>
            </div>
            
            <div class="container">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">1,247</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">42</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">99.9%</div>
                        <div class="stat-label">System Uptime</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">2.1 GB</div>
                        <div class="stat-label">Memory Usage</div>
                    </div>
                </div>
                
                <div class="panel-grid">
                    <div class="panel">
                        <div class="panel-header">System Terminal</div>
                        <div class="panel-content">
                            <div class="terminal">
root@securesystem:~$ whoami<br>
administrator<br><br>
root@securesystem:~$ ps aux | head<br>
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND<br>
root         1  0.0  0.1  225316  9476 ?        Ss   Oct09   0:02 /sbin/init<br>
root         2  0.0  0.0      0     0 ?        S    Oct09   0:00 [kthreadd]<br>
root         3  0.0  0.0      0     0 ?        I&lt;   Oct09   0:00 [rcu_gp]<br><br>
root@securesystem:~$ netstat -tulpn | grep LISTEN<br>
tcp        0      0 0.0.0.0:22          0.0.0.0:*          LISTEN      1047/sshd<br>
tcp        0      0 0.0.0.0:80          0.0.0.0:*          LISTEN      1523/nginx<br>
tcp        0      0 0.0.0.0:443         0.0.0.0:*          LISTEN      1523/nginx<br><br>
root@securesystem:~$ <span style="animation: blink 1s infinite;">_</span>
                            </div>
                            <br>
                            <button class="btn">Execute Command</button>
                            <button class="btn secondary">Clear Terminal</button>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <div class="panel-header">👥 User Management</div>
                        <div class="panel-content">
                            <ul class="user-list">
                                <li>
                                    <span>admin</span>
                                    <span class="user-status">Online</span>
                                </li>
                                <li>
                                    <span>developer</span>
                                    <span class="user-status" style="background: #ffc107; color: #000;">Away</span>
                                </li>
                                <li>
                                    <span>support</span>
                                    <span class="user-status" style="background: #6c757d;">Offline</span>
                                </li>
                            </ul>
                            <br>
                            <button class="btn">Add User</button>
                            <button class="btn secondary">Edit Permissions</button>
                            <button class="btn danger">Delete User</button>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <div class="panel-header">System Settings</div>
                        <div class="panel-content">
                            <p>Configure system parameters and security settings.</p>
                            <br>
                            <button class="btn">Network Config</button>
                            <button class="btn">Security Settings</button>
                            <button class="btn">Backup & Restore</button>
                            <button class="btn secondary">System Logs</button>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <div class="panel-header">System Monitor</div>
                        <div class="panel-content">
                            <p><strong>CPU Usage:</strong> 23%</p>
                            <p><strong>Memory:</strong> 2.1GB / 8GB</p>
                            <p><strong>Disk:</strong> 45GB / 120GB</p>
                            <p><strong>Network:</strong> 1.2 MB/s</p>
                            <br>
                            <button class="btn">View Details</button>
                            <button class="btn secondary">Export Report</button>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''')
    
    @app.route('/logout')
    def logout():
        session.pop('admin_authenticated', None)
        return redirect('/login')
    
    return app

def main():
    print("=" * 60)
    print("HONEYPOT MODULE C - SIMPLE STARTUP")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        print("Creating simple honeypot application...")
        app = create_simple_honeypot()
        
        print("Application created successfully!")
        print()
        
        print("SYSTEM CONFIGURATION:")
        print("   - Server: 0.0.0.0:8080")
        print("   - Geolocation: Basic (localhost detection)")
        print("   - Admin panel: ENABLED")
        print("   - Attack logging: ENABLED")
        print("   - Database: JSON file logging")
        print()
        
        print("ACCESS POINTS:")
        print("   • Main honeypot: http://localhost:8080/login")
        print("   • Fake admin panel: http://localhost:8080/admin/")
        print("   • Admin unlock password: admin123")
        print()
        
        print("SECURITY WARNING:")
        print("   This honeypot is for LAB/EDUCATIONAL USE ONLY!")
        print("   Do not expose to public internet without isolation.")
        print()
        
        print("STARTING SIMPLE HONEYPOT SERVER...")
        print("-" * 60)
        
        # Start the server
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()