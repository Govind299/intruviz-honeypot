#!/usr/bin/env python3
"""
Direct test of geolocation function
"""
import requests
import json

def get_ip_geolocation(ip_address):
    """Test the geolocation function directly"""
    
    # Handle local/private IPs - but get real public IP for testing
    if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith(('192.168.', '10.', '172.')):
        print(f"🏠 Local IP detected ({ip_address}), getting your real public IP for geolocation...")
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
                    'country': 'Local Network',
                    'region': 'Private',
                    'city': 'Localhost', 
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'isp': 'Local Network'
                }
        except Exception as e:
            print(f"Could not get public IP: {e}")
            return {
                'country': 'Local Network',
                'region': 'Private',
                'city': 'Localhost', 
                'latitude': 0.0,
                'longitude': 0.0,
                'isp': 'Local Network'
            }
    
    print(f"🌍 Looking up geolocation for IP: {ip_address}")
    
    # Try ipgeolocation.io first (your premium API key)
    IPGEOLOCATION_API_KEY = "6910ce5a4c184b44b39803b73fd72bf5"
    try:
        url = f'https://api.ipgeolocation.io/ipgeo?apiKey={IPGEOLOCATION_API_KEY}&ip={ip_address}'
        print(f"API URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response Data: {json.dumps(data, indent=2)}")
            
            if not data.get('message'):  # No error message
                result = {
                    'country': data.get('country_name', 'Unknown'),
                    'region': data.get('state_prov', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'latitude': float(data.get('latitude', 0.0)),
                    'longitude': float(data.get('longitude', 0.0)),
                    'isp': data.get('isp', 'Unknown'),
                    'timezone': data.get('time_zone', {}).get('name', 'Unknown') if isinstance(data.get('time_zone'), dict) else data.get('time_zone', 'Unknown'),
                }
                print(f"PREMIUM Geolocation Result: {result}")
                return result
        else:
            print(f"API returned status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Premium API error: {e}")
    
    # Fallback
    return {
        'country': 'API_ERROR',
        'region': 'API_ERROR',
        'city': 'API_ERROR',
        'latitude': 0.0,
        'longitude': 0.0,
        'isp': 'API_ERROR'
    }

if __name__ == '__main__':
    print("🧪 TESTING GEOLOCATION FUNCTION")
    print("=" * 40)
    
    # Test with localhost
    result = get_ip_geolocation('127.0.0.1')
    print(f"\nFinal Result: {result}")