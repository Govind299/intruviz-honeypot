"""
Real-time event broadcasting using Flask-SocketIO
Handles WebSocket connections and event streaming to operator dashboard.
"""
from flask_socketio import SocketIO, emit
import json
from datetime import datetime

# Global SocketIO instance
socketio = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    return socketio

def broadcast_new_event(event_data):
    """Broadcast new event to connected operator clients (non-blocking)"""
    if not socketio:
        return
    
    try:
        # Normalize event data for UI
        normalized_event = {
            'id': str(event_data.get('id', '')),
            'timestamp': event_data.get('timestamp', ''),
            'ip': event_data.get('ip_address', ''),
            'country': event_data.get('country', 'Unknown'),
            'city': event_data.get('city', 'Unknown'),
            'attack_type': event_data.get('attack_type', 'credential_attempt'),
            'endpoint': event_data.get('path', '/login'),
            'user_agent': event_data.get('user_agent', ''),
            'form_data': {
                'username': event_data.get('username', ''),
                'password': event_data.get('password', '')
            },
            'latitude': float(event_data.get('latitude', 0.0)),
            'longitude': float(event_data.get('longitude', 0.0)),
            'method': event_data.get('method', 'POST'),
            'region': event_data.get('region', 'Unknown'),
            'isp': event_data.get('isp', 'Unknown')
        }
        
        # Emit to all connected clients in the events namespace
        socketio.emit('event.new', normalized_event, namespace='/events')
        print(f"Broadcasted new event: {normalized_event['ip']} -> {normalized_event['country']}")
        
    except Exception as e:
        print(f"Socket broadcast error (non-blocking): {e}")

def broadcast_updated_event(event_id, updated_fields):
    """Broadcast event update to connected operator clients (non-blocking)"""
    if not socketio:
        return
    
    try:
        update_payload = {
            'id': event_id,
            'updated_fields': updated_fields,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('event.updated', update_payload, namespace='/events')
        print(f"Broadcasted event update: {event_id}")
        
    except Exception as e:
        print(f"Socket update broadcast error (non-blocking): {e}")

def get_socketio():
    """Get the global SocketIO instance"""
    return socketio
