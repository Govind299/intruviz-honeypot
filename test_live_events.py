"""
Test script to verify the Live Events Feed implementation
Run this after starting the operator dashboard to test the changes
"""

import requests
import json
from datetime import datetime, timedelta

OPERATOR_URL = "http://localhost:5001"
PASSWORD = "operator123"  # Default password from config

def test_login_and_session():
    """Test that login time is stored in session"""
    print("=" * 50)
    print("Test 1: Login and Session Tracking")
    print("=" * 50)
    
    session = requests.Session()
    
    # Login
    login_response = session.post(
        f"{OPERATOR_URL}/operator/login",
        data={"password": PASSWORD}
    )
    
    if login_response.status_code == 200:
        print("✅ Login successful")
        
        # Check dashboard
        dashboard_response = session.get(f"{OPERATOR_URL}/operator")
        if "Logged in:" in dashboard_response.text:
            print("✅ Login time displayed on dashboard")
        else:
            print("❌ Login time not found on dashboard")
    else:
        print("❌ Login failed")
    
    return session

def test_default_filtering(session):
    """Test that events are filtered by login time by default"""
    print("\n" + "=" * 50)
    print("Test 2: Default Filtering by Login Time")
    print("=" * 50)
    
    # Get events without any filters
    response = session.get(f"{OPERATOR_URL}/api/events?limit=100")
    
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        filters = data.get('filters', {})
        
        print(f"✅ API responded successfully")
        print(f"   - Total events returned: {len(events)}")
        print(f"   - Filters applied: {filters}")
        
        if filters.get('since'):
            print(f"✅ Default 'since' filter applied: {filters['since']}")
        else:
            print("⚠️  No 'since' filter applied (might be expected if no login time)")
        
        # Check if all events are after a recent time
        if events:
            oldest_event = min(events, key=lambda e: e.get('timestamp', ''))
            print(f"   - Oldest event timestamp: {oldest_event.get('timestamp', 'N/A')}")
    else:
        print(f"❌ API request failed: {response.status_code}")

def test_custom_filtering(session):
    """Test that custom filters override default behavior"""
    print("\n" + "=" * 50)
    print("Test 3: Custom Filter Override")
    print("=" * 50)
    
    # Set a custom 'since' time (24 hours ago)
    custom_since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    
    response = session.get(
        f"{OPERATOR_URL}/api/events",
        params={"since": custom_since, "limit": 100}
    )
    
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        filters = data.get('filters', {})
        
        print(f"✅ API responded successfully")
        print(f"   - Total events returned: {len(events)}")
        print(f"   - Custom 'since' filter: {filters.get('since', 'N/A')}")
        
        if filters.get('since') == custom_since:
            print("✅ Custom filter correctly applied")
        else:
            print("❌ Custom filter not applied correctly")
    else:
        print(f"❌ API request failed: {response.status_code}")

def test_stats_filtering(session):
    """Test that stats API respects login time"""
    print("\n" + "=" * 50)
    print("Test 4: Stats Filtering")
    print("=" * 50)
    
    response = session.get(f"{OPERATOR_URL}/api/stats?hours=24")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Stats API responded successfully")
        print(f"   - Total events: {data.get('total_events', 'N/A')}")
        print(f"   - Since time: {data.get('since_time', 'N/A')}")
        print(f"   - Top countries: {len(data.get('top_countries', []))}")
        print(f"   - Top IPs: {len(data.get('top_ips', []))}")
    else:
        print(f"❌ Stats API request failed: {response.status_code}")

def main():
    """Run all tests"""
    print("\n🚀 Starting Live Events Feed Tests")
    print(f"Target: {OPERATOR_URL}\n")
    
    try:
        # Test login and session
        session = test_login_and_session()
        
        # Test default filtering
        test_default_filtering(session)
        
        # Test custom filtering
        test_custom_filtering(session)
        
        # Test stats filtering
        test_stats_filtering(session)
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)
        print("\nNext Steps:")
        print("1. Open the operator dashboard in your browser")
        print("2. Run some attack simulations: python test_attacks.py")
        print("3. Watch events appear in real-time (no refresh needed)")
        print("4. Try applying custom filters to see historical data")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to {OPERATOR_URL}")
        print("Make sure the operator dashboard is running:")
        print("  python backend/operator_app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
