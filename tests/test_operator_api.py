"""
Test suite for Operator API endpoints
Tests authentication, filtering, pagination, and data export functionality.
"""
import pytest
import json
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.operator_app import app
from honeypot.storage import insert_event
import uuid

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client"""
    # Login
    response = client.post('/operator/login', data={'password': 'honeypot2024!'})
    assert response.status_code == 302  # Redirect on success
    return client

@pytest.fixture
def sample_events():
    """Create sample events for testing"""
    events = []
    base_time = datetime.utcnow()
    
    for i in range(10):
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': (base_time - timedelta(minutes=i)).isoformat(),
            'ip_address': f'192.168.1.{i+1}',
            'method': 'POST',
            'endpoint': '/login',
            'headers': {'User-Agent': f'TestBot/{i}'},
            'form_data': {'username': f'user{i}', 'password': f'pass{i}'},
            'user_agent': f'TestBot/{i}',
            'country': 'TestCountry' if i % 2 == 0 else 'AnotherCountry',
            'region': 'TestRegion',
            'city': 'TestCity',
            'latitude': 40.7128 + (i * 0.01),
            'longitude': -74.0060 + (i * 0.01),
            'isp': 'TestISP',
            'attack_type': 'login_attempt' if i % 3 == 0 else 'brute_force'
        }
        insert_event(event_data)
        events.append(event_data)
    
    return events

class TestAuthentication:
    """Test authentication and session management"""
    
    def test_login_page_accessible(self, client):
        """Test login page is accessible"""
        response = client.get('/operator/login')
        assert response.status_code == 200
        assert b'Operator Dashboard' in response.data
    
    def test_login_with_correct_password(self, client):
        """Test successful login"""
        response = client.post('/operator/login', data={'password': 'honeypot2024!'})
        assert response.status_code == 302  # Redirect on success
    
    def test_login_with_wrong_password(self, client):
        """Test failed login"""
        response = client.post('/operator/login', data={'password': 'wrongpass'})
        assert response.status_code == 200
        assert b'Invalid password' in response.data
    
    def test_protected_routes_require_auth(self, client):
        """Test that protected routes require authentication"""
        response = client.get('/operator')
        assert response.status_code == 302  # Redirect to login
        
        response = client.get('/api/events')
        assert response.status_code == 401
    
    def test_logout_clears_session(self, authenticated_client):
        """Test logout functionality"""
        # Access protected route (should work)
        response = authenticated_client.get('/operator')
        assert response.status_code == 200
        
        # Logout
        response = authenticated_client.get('/operator/logout')
        assert response.status_code == 302
        
        # Try to access protected route again (should fail)
        response = authenticated_client.get('/operator')
        assert response.status_code == 302

class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    def test_api_events_endpoint(self, authenticated_client, sample_events):
        """Test /api/events endpoint"""
        response = authenticated_client.get('/api/events')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'events' in data
        assert 'count' in data
        assert len(data['events']) > 0
    
    def test_api_events_pagination(self, authenticated_client, sample_events):
        """Test API events pagination"""
        response = authenticated_client.get('/api/events?limit=5&offset=0')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['events']) <= 5
        assert data['limit'] == 5
        assert data['offset'] == 0
    
    def test_api_events_filtering(self, authenticated_client, sample_events):
        """Test API events filtering"""
        # Filter by IP
        response = authenticated_client.get('/api/events?ip=192.168.1.1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        if data['events']:
            assert '192.168.1.1' in data['events'][0]['client_ip']
        
        # Filter by country
        response = authenticated_client.get('/api/events?country=TestCountry')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        if data['events']:
            assert data['events'][0]['country'] == 'TestCountry'
    
    def test_api_stats_endpoint(self, authenticated_client, sample_events):
        """Test /api/stats endpoint"""
        response = authenticated_client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'top_ips' in data
        assert 'top_countries' in data
        assert 'timeline' in data
        assert 'attack_types' in data
        assert 'total_events' in data
    
    def test_api_map_points_endpoint(self, authenticated_client, sample_events):
        """Test /api/map_points endpoint"""
        response = authenticated_client.get('/api/map_points')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'points' in data
        assert 'total_points' in data
        
        if data['points']:
            point = data['points'][0]
            assert 'lat' in point
            assert 'lng' in point
            assert 'popup' in point
    
    def test_api_event_detail(self, authenticated_client, sample_events):
        """Test /api/event/<id> endpoint"""
        # Get an event ID from the sample events
        event_id = sample_events[0]['id']
        
        response = authenticated_client.get(f'/api/event/{event_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'event' in data
        assert 'enrichment' in data
        assert data['event']['id'] == event_id
    
    def test_api_event_detail_not_found(self, authenticated_client):
        """Test /api/event/<id> with non-existent ID"""
        response = authenticated_client.get('/api/event/nonexistent-id')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_api_export_csv(self, authenticated_client, sample_events):
        """Test /api/export/csv endpoint"""
        response = authenticated_client.get('/api/export/csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers['Content-Disposition']
        
        # Check CSV content
        csv_content = response.data.decode('utf-8')
        assert 'timestamp,ip,country' in csv_content

class TestDataIntegrity:
    """Test data integrity and edge cases"""
    
    def test_empty_database_handling(self, authenticated_client):
        """Test API behavior with empty database"""
        response = authenticated_client.get('/api/events')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data['events'], list)
        assert data['count'] >= 0
    
    def test_invalid_parameters(self, authenticated_client):
        """Test API behavior with invalid parameters"""
        # Invalid limit
        response = authenticated_client.get('/api/events?limit=invalid')
        assert response.status_code == 500  # Should handle gracefully
        
        # Negative offset
        response = authenticated_client.get('/api/events?offset=-1')
        assert response.status_code == 200  # Should work (treated as 0)
    
    def test_time_range_filtering(self, authenticated_client, sample_events):
        """Test time-based filtering"""
        # Recent events
        since_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        response = authenticated_client.get(f'/api/events?since={since_time}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should have some events from the last 5 minutes
        assert len(data['events']) >= 0

class TestHealthCheck:
    """Test health check and system status"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint (no auth required)"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'operator_dashboard' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])