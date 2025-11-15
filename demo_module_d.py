#!/usr/bin/env python3
"""
Module D Demo Script - Complete System Test
Demonstrates the full honeypot + operator dashboard integration.
"""
import requests
import time
import json
import sys
import os
from datetime import datetime
import uuid

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from honeypot.storage import insert_event
from backend.socket_bridge import broadcast_new_event

def create_demo_event(ip, country, city, attack_type, username, password):
    """Create a demo attack event"""
    return {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': ip,
        'method': 'POST',
        'endpoint': '/login',
        'headers': {
            'User-Agent': 'DemoBot/1.0',
            'Accept': 'text/html,application/xhtml+xml'
        },
        'form_data': {
            'username': username,
            'password': password
        },
        'user_agent': 'DemoBot/1.0 (Demo Attack Simulation)',
        'country': country,
        'region': f'{country} Region',
        'city': city,
        'latitude': 40.7128 + (hash(city) % 100) * 0.01,
        'longitude': -74.0060 + (hash(city) % 100) * 0.01,
        'isp': f'{country} ISP',
        'attack_type': attack_type
    }

def test_honeypot_running():
    """Test if honeypot is running"""
    try:
        response = requests.get('http://localhost:8080/login', timeout=5)
        return response.status_code == 200
    except:
        return False

def test_dashboard_running():
    """Test if dashboard is running"""
    try:
        response = requests.get('http://127.0.0.1:8090/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def simulate_realistic_attacks():
    """Simulate realistic attack scenarios"""
    
    print("🎭 Simulating realistic attack scenarios...")
    
    # Different attack scenarios
    scenarios = [
        {
            'ip': '198.51.100.42',
            'country': 'Russia',
            'city': 'Moscow',
            'attack_type': 'brute_force',
            'username': 'admin',
            'password': 'password'
        },
        {
            'ip': '203.0.113.195',
            'country': 'China', 
            'city': 'Beijing',
            'attack_type': 'credential_stuffing',
            'username': 'administrator',
            'password': '123456'
        },
        {
            'ip': '192.0.2.146',
            'country': 'United States',
            'city': 'New York',
            'attack_type': 'sql_injection',
            'username': "admin'; DROP TABLE users; --",
            'password': 'anything'
        },
        {
            'ip': '198.51.100.89',
            'country': 'Germany',
            'city': 'Berlin',
            'attack_type': 'dictionary_attack',
            'username': 'root',
            'password': 'toor'
        },
        {
            'ip': '203.0.113.33',
            'country': 'Brazil',
            'city': 'São Paulo', 
            'attack_type': 'brute_force',
            'username': 'admin',
            'password': 'admin123'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"  Attack {i}/5: {scenario['country']} ({scenario['ip']}) - {scenario['attack_type']}")
        
        # Create event
        event = create_demo_event(**scenario)
        
        # Insert into database
        insert_event(event)
        
        # Broadcast to real-time dashboard
        try:
            broadcast_new_event(event)
            print(f"    Event broadcasted to dashboard")
        except Exception as e:
            print(f"    Dashboard broadcast failed: {e}")
        
        # Also send to honeypot if running
        if test_honeypot_running():
            try:
                response = requests.post('http://localhost:8080/login', 
                                       data={
                                           'username': scenario['username'],
                                           'password': scenario['password']
                                       }, 
                                       timeout=5)
                print(f"    Sent to honeypot (status: {response.status_code})")
            except Exception as e:
                print(f"    Honeypot request failed: {e}")
        
        time.sleep(2)  # Realistic timing
    
    print("Attack simulation completed!")

def test_dashboard_api():
    """Test dashboard API endpoints"""
    
    print("Testing Dashboard API...")
    
    if not test_dashboard_running():
        print("Dashboard not running - start with: python backend/operator_app.py")
        return False
    
    # Test health endpoint
    try:
        response = requests.get('http://127.0.0.1:8090/health', timeout=5)
        if response.status_code == 200:
            print("  Health check passed")
            health_data = response.json()
            print(f"    Status: {health_data.get('status')}")
            print(f"    Version: {health_data.get('operator_dashboard')}")
        else:
            print(f"  Health check failed: {response.status_code}")
    except Exception as e:
        print(f"  Health check error: {e}")
    
    # Note: API endpoints require authentication, so we can't test them directly
    # without implementing session handling
    print("  ℹ️ API endpoints require authentication - test manually via dashboard")
    
    return True

def main():
    """Main demo function"""
    
    print("HONEYPOT MODULE D - COMPLETE SYSTEM DEMO")
    print("=" * 50)
    print("LAB/EDUCATIONAL USE ONLY - DO NOT EXPOSE TO INTERNET")
    print("=" * 50)
    
    # Check system status
    print("\nChecking System Status...")
    
    honeypot_running = test_honeypot_running()
    dashboard_running = test_dashboard_running()
    
    print(f"  Honeypot (port 8080): {'Running' if honeypot_running else 'Not running'}")
    print(f"  Dashboard (port 8090): {'Running' if dashboard_running else 'Not running'}")
    
    if not honeypot_running:
        print("\nTo start honeypot: python simple_honeypot.py")
    
    if not dashboard_running:
        print("\nTo start dashboard: python backend/operator_app.py")
        print("   Dashboard URL: http://127.0.0.1:8090/operator")
        print("   Password: honeypot2024!")
    
    # Ask user if they want to continue with demo
    if not (honeypot_running or dashboard_running):
        print("\nNeither component is running. Start them first to see the full demo.")
        return
    
    print(f"\nReady to demonstrate with {'both components' if honeypot_running and dashboard_running else 'partial system'}")
    
    try:
        input("Press Enter to start attack simulation...")
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
        return
    
    # Run attack simulation
    simulate_realistic_attacks()
    
    # Test dashboard API
    if dashboard_running:
        test_dashboard_api()
    
    # Final instructions
    print("\nDemo Complete! Next Steps:")
    print("=" * 50)
    
    if dashboard_running:
        print("1. Open dashboard: http://127.0.0.1:8090/operator")
        print("2. Login with password: honeypot2024!")
        print("3. View real-time events, charts, and map")
        print("4. Click on events for detailed analysis")
        print("5. Export data using CSV export feature")
    
    if honeypot_running:
        print("\nHoneypot Access Points:")
        print("   • Main honeypot: http://localhost:8080/login")
        print("   • Admin panel: http://localhost:8080/admin/ (password: admin123)")
    
    print("\nAdditional Testing:")
    print("   • Run tests: python -m pytest tests/ -v")
    print("   • API testing: python tests/test_operator_api.py")
    print("   • Manual attacks: python test_attacks.py")
    
    print(f"\n⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()