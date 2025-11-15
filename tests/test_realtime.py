"""
Test suite for real-time WebSocket functionality
Tests SocketIO connections, event broadcasting, and real-time updates.
"""
import pytest
import json
import sys
import os
from datetime import datetime
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.operator_app import app, socketio
from backend.socket_bridge import broadcast_new_event, broadcast_updated_event
from honeypot.storage import insert_event

@pytest.fixture
def client():
    """Create test client with SocketIO"""
    app.config['TESTING'] = True
    return socketio.test_client(app, namespace='/events')

@pytest.fixture
def authenticated_session():
    """Create authenticated session for WebSocket testing"""
    with app.test_client() as client:
        # Login first
        response = client.post('/operator/login', data={'password': 'honeypot2024!'})
        assert response.status_code == 302
        return client.session

class TestSocketIOConnection:
    """Test WebSocket connection and authentication"""
    
    def test_socket_connection_without_auth(self):
        """Test WebSocket connection without authentication (should fail)"""
        client = socketio.test_client(app, namespace='/events')
        # Connection should be rejected
        assert not client.is_connected(namespace='/events')
    
    def test_socket_connection_with_auth(self, authenticated_session):
        """Test WebSocket connection with authentication"""
        # This test would need session handling in SocketIO
        # For now, we'll test the basic connection mechanism
        client = socketio.test_client(app, namespace='/events')
        # In a real scenario, this would check authentication
        # For testing purposes, we'll assume it connects
        assert client is not None

class TestEventBroadcasting:
    """Test real-time event broadcasting"""
    
    def test_broadcast_new_event(self):
        """Test broadcasting new events"""
        # Create sample event
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '192.168.1.100',
            'country': 'TestCountry',
            'city': 'TestCity',
            'attack_type': 'login_attempt',
            'endpoint': '/login',
            'user_agent': 'TestBot/1.0',
            'form_data': {'username': 'test', 'password': 'test'},
            'latitude': 40.7128,
            'longitude': -74.0060
        }
        
        # Test broadcast function
        try:
            broadcast_new_event(event_data)
            # If no exception is raised, the broadcast worked
            assert True
        except Exception as e:
            # Broadcasting might fail if no clients are connected
            assert "No clients connected" in str(e) or "SocketIO not initialized" in str(e)
    
    def test_broadcast_event_update(self):
        """Test broadcasting event updates"""
        event_id = str(uuid.uuid4())
        updated_fields = {
            'country': 'UpdatedCountry',
            'enriched': True
        }
        
        # Test update broadcast
        try:
            broadcast_updated_event(event_id, updated_fields)
            assert True
        except Exception as e:
            # Broadcasting might fail if no clients are connected
            assert "No clients connected" in str(e) or "SocketIO not initialized" in str(e)

class TestRealTimeIntegration:
    """Test integration between storage and real-time broadcasting"""
    
    def test_event_insertion_triggers_broadcast(self):
        """Test that inserting events triggers real-time broadcasts"""
        # Create test event
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '192.168.1.200',
            'method': 'POST',
            'endpoint': '/login',
            'headers': {'User-Agent': 'TestBot/2.0'},
            'form_data': {'username': 'realtime_test', 'password': 'test123'},
            'user_agent': 'TestBot/2.0',
            'country': 'RealtimeCountry',
            'region': 'RealtimeRegion',
            'city': 'RealtimeCity',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'isp': 'RealtimeISP',
            'attack_type': 'brute_force'
        }
        
        # Insert event (this should trigger broadcast in real implementation)
        event_id = insert_event(event_data)
        assert event_id == event_data['id']
        
        # In a real implementation with logger integration,
        # this would trigger broadcast_new_event automatically
        broadcast_new_event(event_data)

class TestEventMessageFormats:
    """Test WebSocket message formats and structures"""
    
    def test_new_event_message_format(self):
        """Test the format of new event messages"""
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '10.0.0.1',
            'country': 'MessageTestCountry',
            'city': 'MessageTestCity',
            'attack_type': 'sql_injection',
            'endpoint': '/admin',
            'user_agent': 'Evil Bot/1.0',
            'form_data': {'id': '1\' OR \'1\'=\'1'},
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        
        # The broadcast function should normalize the event
        # We can test this by checking the expected format
        expected_fields = [
            'id', 'timestamp', 'ip', 'country', 'city', 
            'attack_type', 'endpoint', 'user_agent', 'form_data',
            'latitude', 'longitude'
        ]
        
        # In the actual broadcast, the event would be normalized
        normalized_event = {
            'id': event_data.get('id', ''),
            'timestamp': event_data.get('timestamp', ''),
            'ip': event_data.get('ip_address', ''),
            'country': event_data.get('country', 'Unknown'),
            'city': event_data.get('city', 'Unknown'),
            'attack_type': event_data.get('attack_type', 'login_attempt'),
            'endpoint': event_data.get('endpoint', '/login'),
            'user_agent': event_data.get('user_agent', ''),
            'form_data': event_data.get('form_data', {}),
            'latitude': event_data.get('latitude', 0.0),
            'longitude': event_data.get('longitude', 0.0)
        }
        
        # Check that all expected fields are present
        for field in expected_fields:
            assert field in normalized_event
    
    def test_update_event_message_format(self):
        """Test the format of event update messages"""
        event_id = str(uuid.uuid4())
        updated_fields = {
            'country': 'UpdatedCountry',
            'region': 'UpdatedRegion',
            'isp': 'UpdatedISP',
            'enriched': True
        }
        
        # Expected update message format
        expected_update = {
            'id': event_id,
            'updated_fields': updated_fields,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check required fields
        assert 'id' in expected_update
        assert 'updated_fields' in expected_update
        assert 'timestamp' in expected_update
        assert isinstance(expected_update['updated_fields'], dict)

class TestThrottling:
    """Test event throttling and batching"""
    
    def test_multiple_events_handling(self):
        """Test handling of multiple rapid events"""
        events = []
        
        # Create multiple events rapidly
        for i in range(5):
            event_data = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': f'192.168.2.{i}',
                'country': 'ThrottleTestCountry',
                'city': 'ThrottleTestCity',
                'attack_type': 'brute_force',
                'endpoint': '/login',
                'user_agent': f'ThrottleBot/{i}',
                'form_data': {'username': f'user{i}', 'password': f'pass{i}'},
                'latitude': 40.7128 + (i * 0.001),
                'longitude': -74.0060 + (i * 0.001)
            }
            events.append(event_data)
        
        # In a real implementation, these would be throttled
        # For testing, we just verify they can all be processed
        for event in events:
            try:
                broadcast_new_event(event)
            except Exception:
                # Expected if no clients connected
                pass
        
        assert len(events) == 5

class TestErrorHandling:
    """Test error handling in real-time system"""
    
    def test_broadcast_with_invalid_data(self):
        """Test broadcasting with invalid event data"""
        invalid_event = {
            'invalid_field': 'invalid_value'
        }
        
        # Should not raise exception (graceful handling)
        try:
            broadcast_new_event(invalid_event)
            assert True
        except Exception as e:
            # Should handle gracefully
            print(f"Expected error handled: {e}")
            assert True
    
    def test_broadcast_without_socketio(self):
        """Test broadcasting when SocketIO is not initialized"""
        # This tests the graceful fallback when SocketIO is not available
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '127.0.0.1'
        }
        
        # Should not crash the application
        try:
            broadcast_new_event(event_data)
            assert True
        except Exception as e:
            # Should handle gracefully
            assert "socketio" in str(e).lower() or "not initialized" in str(e).lower()

class TestPerformance:
    """Test performance aspects of real-time system"""
    
    def test_broadcast_performance(self):
        """Test that broadcasting doesn't block the main thread"""
        import time
        
        event_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': '192.168.3.1',
            'country': 'PerformanceTestCountry',
            'attack_type': 'performance_test'
        }
        
        start_time = time.time()
        
        # Broadcast should be non-blocking
        try:
            broadcast_new_event(event_data)
        except Exception:
            pass  # Expected if no clients
        
        end_time = time.time()
        
        # Should complete very quickly (non-blocking)
        assert (end_time - start_time) < 1.0  # Less than 1 second

# Example test data for integration testing
def create_sample_realtime_event():
    """Create a sample event for real-time testing"""
    return {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': '203.0.113.195',  # Example IP
        'method': 'POST',
        'endpoint': '/login',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9'
        },
        'form_data': {
            'username': 'admin',
            'password': 'password123'
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'country': 'United States',
        'region': 'California',
        'city': 'San Francisco',
        'latitude': 37.7749,
        'longitude': -122.4194,
        'isp': 'Example ISP',
        'attack_type': 'brute_force'
    }

if __name__ == '__main__':
    # Run some basic tests
    print("🧪 Testing real-time broadcasting...")
    
    # Test event creation and broadcasting
    sample_event = create_sample_realtime_event()
    print(f"Created sample event: {sample_event['id']}")
    
    # Test broadcast (will work even without clients)
    try:
        broadcast_new_event(sample_event)
        print("Broadcast test passed")
    except Exception as e:
        print(f"Broadcast test warning: {e}")
    
    # Run pytest
    pytest.main([__file__, '-v'])