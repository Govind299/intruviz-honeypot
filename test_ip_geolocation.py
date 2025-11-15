#!/usr/bin/env python3
"""
Test IP Geolocation - Shows the difference between local and real IP geolocation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_honeypot import get_ip_geolocation

def test_geolocation():
    print("🧪 TESTING IP GEOLOCATION SYSTEM")
    print("=" * 50)
    
    # Test 1: Local IP (should use manual override - Nadiad)
    print("\n1️⃣ Testing LOCAL IP (127.0.0.1):")
    print("-" * 30)
    local_result = get_ip_geolocation('127.0.0.1')
    print(f"Result: {local_result['city']}, {local_result['region']}, {local_result['country']}")
    
    # Test 2: Real external IP (should use actual geolocation)
    print("\n2️⃣ Testing REAL external IP (Google DNS 8.8.8.8):")
    print("-" * 30)
    real_result = get_ip_geolocation('8.8.8.8')
    print(f"Result: {real_result['city']}, {real_result['region']}, {real_result['country']}")
    
    # Test 3: Another real IP (Cloudflare DNS)
    print("\n3️⃣ Testing REAL external IP (Cloudflare 1.1.1.1):")
    print("-" * 30)
    cf_result = get_ip_geolocation('1.1.1.1')
    print(f"Result: {cf_result['city']}, {cf_result['region']}, {cf_result['country']}")
    
    print("\nSUMMARY:")
    print(f"• Local IP: Uses manual override → {local_result['city']}")
    print(f"• Real IPs: Use actual geolocation API → {real_result['city']}, {cf_result['city']}")
    print(f"• This way, attacking IPs get REAL location data!")

if __name__ == "__main__":
    test_geolocation()