import requests
import time

#!/usr/bin/env python3

print("Testing Honeypot with Premium Geolocation")
print("=" * 45)

attacks = [
    {"username": "admin", "password": "password123", "type": "Brute Force"},
    {"username": "hacker", "password": "letmein", "type": "Dictionary Attack"},
    {"username": "admin", "password": "admin123", "type": "Admin Unlock"}
]

for i, attack in enumerate(attacks, 1):
    print(f"\nAttack {i}: {attack['type']} - {attack['username']}:{attack['password']}")
    
    try:
        response = requests.post("http://127.0.0.1:8080/login", 
            data={"username": attack["username"], "password": attack["password"]}, 
            timeout=15
        )
        print(f"Response: {response.status_code}")
        time.sleep(3)  # Wait for geolocation lookup
    except Exception as e:
        print(f"Error: {e}")

print("\nAttack simulation completed!")
print("Check honeypot logs for premium geolocation data")