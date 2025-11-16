#!/usr/bin/env python3
"""
Test script to demonstrate different attack types
"""
import requests
import time

HONEYPOT_URL = "http://127.0.0.1:8080/login"

attacks = [
    # SQL Injection attacks
    {"username": "admin' OR '1'='1", "password": "anything", "type": "SQL Injection #1"},
    {"username": "admin", "password": "' OR 1=1--", "type": "SQL Injection #2"},
    {"username": "user'; DROP TABLE users--", "password": "pass", "type": "SQL Injection #3"},
    {"username": "admin' UNION SELECT * FROM users--", "password": "test", "type": "SQL Injection #4"},
    
    # XSS attacks
    {"username": "<script>alert('XSS')</script>", "password": "test", "type": "XSS #1"},
    {"username": "user", "password": "<img src=x onerror=alert('XSS')>", "type": "XSS #2"},
    {"username": "admin", "password": "javascript:alert(1)", "type": "XSS #3"},
    
    # Command Injection
    {"username": "admin; ls -la", "password": "test", "type": "Command Injection #1"},
    {"username": "user && whoami", "password": "pass", "type": "Command Injection #2"},
    {"username": "admin | cat /etc/passwd", "password": "test", "type": "Command Injection #3"},
    
    # LDAP Injection
    {"username": "admin*)(uid=*", "password": "test", "type": "LDAP Injection #1"},
    {"username": "user)(cn=*", "password": "pass", "type": "LDAP Injection #2"},
    
    # Admin Unlock
    {"username": "admin", "password": "admin123", "type": "Admin Unlock Attempt"},
    
    # Brute Force (common passwords)
    {"username": "admin", "password": "123456", "type": "Brute Force #1"},
    {"username": "root", "password": "password", "type": "Brute Force #2"},
    {"username": "user", "password": "admin", "type": "Brute Force #3"},
    {"username": "admin", "password": "qwerty", "type": "Brute Force #4"},
    
    # Regular login attempts
    {"username": "john.doe", "password": "MyP@ssw0rd!", "type": "Normal Login Attempt #1"},
    {"username": "alice", "password": "SecurePass2024", "type": "Normal Login Attempt #2"},
]

print("🎯 Testing Different Attack Types on Honeypot")
print("=" * 60)

for i, attack in enumerate(attacks, 1):
    try:
        print(f"\n[{i}/{len(attacks)}] {attack['type']}")
        print(f"   Username: {attack['username'][:50]}")
        print(f"   Password: {attack['password'][:50]}")
        
        response = requests.post(
            HONEYPOT_URL,
            data={
                'username': attack['username'],
                'password': attack['password']
            },
            headers={
                'User-Agent': 'python-requests/2.32.4 (AttackTypeTest)'
            },
            timeout=5
        )
        
        print(f"   ✓ Response: {response.status_code}")
        time.sleep(0.5)  # Small delay between attacks
        
    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("✅ Attack type testing complete!")
print("Check the Live Operator Dashboard to see different attack types.")
print("Go to: http://127.0.0.1:5001/live/")
