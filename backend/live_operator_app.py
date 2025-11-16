"""
LIVE OPERATOR DASHBOARD - Shows ONLY live attacks after login
Clean implementation with proper session management
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from functools import wraps
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeypot import storage
from backend.api_tools import get_dashboard_stats, get_map_data

app = Flask(__name__, 
           template_folder='../frontend/operator_templates',
           static_folder='../frontend/operator_static')
app.config['SECRET_KEY'] = 'live-honeypot-super-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configuration
OPERATOR_PASSWORD = 'honeypot2024!'
SECURITY_WARNING = 'LAB/EDUCATIONAL USE ONLY - DO NOT EXPOSE TO INTERNET'

def require_auth():
    """Check if user is authenticated"""
    return session.get('live_operator_authenticated', False)

@app.before_request
def check_auth():
    """Require authentication for all routes except login"""
    if request.endpoint and 'login' not in request.endpoint and 'static' not in request.endpoint:
        if not require_auth():
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))

# Authentication routes
@app.route('/live/login', methods=['GET', 'POST'])
def login():
    """Live operator login page and authentication"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == OPERATOR_PASSWORD:
            session['live_operator_authenticated'] = True
            # Set login time to RIGHT NOW
            session['live_login_time'] = datetime.utcnow().isoformat()
            print(f"✅ Live operator logged in at {session['live_login_time']}")
            return redirect(url_for('live_dashboard'))
        else:
            return render_template('live_login.html', error='Invalid password', security_warning=SECURITY_WARNING)
    
    return render_template('live_login.html', security_warning=SECURITY_WARNING)

@app.route('/live/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/live')
@app.route('/live/')
def live_dashboard():
    """Live operator dashboard - ONLY shows events after login"""
    login_time = session.get('live_login_time', datetime.utcnow().isoformat())
    return render_template('live_dashboard.html', 
                         security_warning=SECURITY_WARNING,
                         login_time=login_time)

# API routes
@app.route('/api/live/events')
def api_live_events():
    """Get events - ONLY after login time"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # ALWAYS filter by login time
    login_time = session.get('live_login_time')
    
    if not login_time:
        return jsonify({
            'events': [],
            'count': 0,
            'message': 'No login time found'
        })
    
    # Get events ONLY after login time
    events = storage.query_recent(
        limit=limit,
        offset=offset,
        filters={'since': login_time}
    )
    
    print(f"📊 Returning {len(events)} events after {login_time}")
    
    return jsonify({
        'events': events,
        'limit': limit,
        'offset': offset,
        'count': len(events),
        'filters': {'since': login_time}
    })

@app.route('/api/live/stats')
def api_live_stats():
    """Get dashboard statistics - ONLY after login time"""
    login_time = session.get('live_login_time')
    
    if not login_time:
        return jsonify({'error': 'No login time'})
    
    stats = get_dashboard_stats(since_hours=24, since_time=login_time)
    return jsonify(stats)

@app.route('/api/live/map_points')
def api_live_map():
    """Get map data - ONLY after login time"""
    login_time = session.get('live_login_time')
    limit = int(request.args.get('limit', 1000))
    
    if not login_time:
        return jsonify({'points': []})
    
    map_data = get_map_data(since_hours=24, limit=limit, since_time=login_time)
    return jsonify(map_data)

# SocketIO event handlers
@socketio.on('connect', namespace='/live')
def handle_live_connect():
    """Handle client connection to live events namespace"""
    if not require_auth():
        return False  # Reject connection
    print(f"✅ Live operator client connected")

@socketio.on('disconnect', namespace='/live')
def handle_live_disconnect():
    """Handle client disconnection"""
    print(f"❌ Live operator client disconnected")

@socketio.on('request_recent', namespace='/live')
def handle_live_request_recent(data):
    """Handle request for recent events - ONLY after login time"""
    limit = data.get('limit', 10)
    login_time = session.get('live_login_time')
    
    if not login_time:
        socketio.emit('recent_events', {
            'events': [],
            'count': 0,
            'message': 'No login time'
        }, namespace='/live')
        return
    
    # Get events ONLY after login time
    recent_events = storage.query_recent(
        limit=limit,
        offset=0,
        filters={'since': login_time}
    )
    
    print(f"📡 WebSocket: Sending {len(recent_events)} events after {login_time}")
    
    socketio.emit('recent_events', {
        'events': recent_events,
        'limit': limit,
        'offset': 0,
        'count': len(recent_events),
        'filters': {'since': login_time}
    }, namespace='/live')

# Broadcast new events to all connected clients
def broadcast_new_event(event_data):
    """Broadcast new event to all connected live operator clients"""
    socketio.emit('event.new', event_data, namespace='/live', broadcast=True)

# Health check
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'dashboard': 'Live Operator Dashboard'
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("LIVE OPERATOR DASHBOARD - REAL-TIME ONLY")
    print("="*50)
    print(f"WARNING: {SECURITY_WARNING}")
    print(f"Operator Password: {OPERATOR_PASSWORD}")
    print(f"Dashboard URL: http://127.0.0.1:5001/live")
    print(f"API Base URL: http://127.0.0.1:5001/api/live")
    print(f"WebSocket: ws://127.0.0.1:5001/live")
    print("="*50 + "\n")
    
    socketio.run(app, host='127.0.0.1', port=5001, debug=True)
