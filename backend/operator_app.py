"""
Flask Operator Dashboard App - Module D
Secure operator interface for real-time honeypot monitoring and analytics.
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from flask_socketio import SocketIO
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from honeypot.config import (
    OPERATOR_PASSWORD, OPERATOR_BIND, OPERATOR_PORT, 
    OPERATOR_SESSION_SECRET, SECURITY_WARNING
)
from backend.socket_bridge import init_socketio
from backend.api_tools import (
    get_dashboard_stats, get_filtered_events, 
    get_map_data, export_events_csv, get_event_detail
)

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../frontend/operator_templates',
           static_folder='../frontend/operator_static')

app.config['SECRET_KEY'] = OPERATOR_SESSION_SECRET
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS

# Initialize SocketIO
socketio = init_socketio(app)

def require_auth():
    """Check if user is authenticated"""
    return session.get('operator_authenticated', False)

@app.before_request
def check_auth():
    """Enforce authentication on protected routes"""
    # Skip authentication check for login page and health endpoint
    if request.path in ['/operator/login', '/health'] or request.path.startswith('/static'):
        return
    
    protected_routes = ['/operator', '/api/']
    
    if any(request.path.startswith(route) for route in protected_routes):
        if not require_auth():
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))

# Authentication routes
@app.route('/operator/login', methods=['GET', 'POST'])
def login():
    """Operator login page and authentication"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == OPERATOR_PASSWORD:
            session['operator_authenticated'] = True
            session['login_time'] = datetime.utcnow().isoformat()
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid password', security_warning=SECURITY_WARNING)
    
    return render_template('login.html', security_warning=SECURITY_WARNING)

@app.route('/operator/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/operator')
@app.route('/operator/')
def dashboard():
    """Main operator dashboard"""
    return render_template('dashboard.html', 
                         security_warning=SECURITY_WARNING,
                         login_time=session.get('login_time', ''))

@app.route('/operator/event/<event_id>')
def event_detail(event_id):
    """Event detail page"""
    return render_template('event_detail.html', 
                         event_id=event_id,
                         security_warning=SECURITY_WARNING)

# API routes
@app.route('/api/events')
def api_events():
    """Get filtered events with pagination"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    since = request.args.get('since', '')
    ip = request.args.get('ip', '')
    country = request.args.get('country', '')
    attack_type = request.args.get('type', '')
    
    # If no 'since' filter is provided and user is logged in, 
    # default to showing only events after login time
    if not since and session.get('login_time'):
        since = session.get('login_time')
    
    result = get_filtered_events(
        limit=limit, offset=offset, since=since,
        ip=ip, country=country, attack_type=attack_type
    )
    
    return jsonify(result)

@app.route('/api/event/<event_id>')
def api_event_detail(event_id):
    """Get detailed event information"""
    result = get_event_detail(event_id)
    return jsonify(result)

@app.route('/api/stats')
def api_stats():
    """Get dashboard statistics"""
    hours = int(request.args.get('hours', 24))
    # Use login time as baseline if available
    since_time = request.args.get('since', session.get('login_time', ''))
    stats = get_dashboard_stats(since_hours=hours, since_time=since_time)
    return jsonify(stats)

@app.route('/api/map_points')
def api_map_points():
    """Get geolocation points for map visualization"""
    hours = int(request.args.get('hours', 24))
    limit = int(request.args.get('limit', 1000))
    # Use login time as baseline if available
    since_time = request.args.get('since', session.get('login_time', ''))
    
    map_data = get_map_data(since_hours=hours, limit=limit, since_time=since_time)
    return jsonify(map_data)

@app.route('/api/notify_event', methods=['POST'])
def api_notify_event():
    """Receive real-time event notifications from honeypot"""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No event data provided'}), 400
        
        # Broadcast to all connected WebSocket clients
        socketio.emit('event.new', event_data, namespace='/events')
        
        print(f"📡 Broadcasted event: {event_data.get('ip', 'unknown')} -> {event_data.get('country', 'unknown')}")
        
        return jsonify({'status': 'success', 'message': 'Event broadcasted'}), 200
        
    except Exception as e:
        print(f"❌ Event notification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def api_export_csv():
    """Export events as CSV"""
    filters = {
        'since': request.args.get('since', ''),
        'ip': request.args.get('ip', ''),
        'country': request.args.get('country', ''),
        'type': request.args.get('type', '')
    }
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    csv_data = export_events_csv(filters)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=honeypot_events_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# SocketIO event handlers
@socketio.on('connect', namespace='/events')
def handle_connect():
    """Handle client connection to events namespace"""
    if not require_auth():
        return False  # Reject connection
    print(f"Operator client connected to real-time events")

@socketio.on('disconnect', namespace='/events')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Operator client disconnected from real-time events")

@socketio.on('request_recent', namespace='/events')
def handle_request_recent(data):
    """Handle request for recent events"""
    limit = data.get('limit', 10)
    # Only show events after login time by default
    since = session.get('login_time', '')
    recent_events = get_filtered_events(limit=limit, offset=0, since=since)
    socketio.emit('recent_events', recent_events, namespace='/events')

# Health check
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'operator_dashboard': 'Module D',
        'version': '1.0.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("HONEYPOT OPERATOR DASHBOARD - MODULE D")
    print("=" * 50)
    print(f"WARNING: {SECURITY_WARNING}")
    print(f"Operator Password: {OPERATOR_PASSWORD}")
    print(f"Dashboard URL: http://{OPERATOR_BIND}:{OPERATOR_PORT}/operator")
    print(f"API Base URL: http://{OPERATOR_BIND}:{OPERATOR_PORT}/api")
    print(f"WebSocket: ws://{OPERATOR_BIND}:{OPERATOR_PORT}/ws/events")
    print("=" * 50)
    
    # Run with SocketIO
    socketio.run(app, 
                host=OPERATOR_BIND, 
                port=OPERATOR_PORT, 
                debug=False,
                allow_unsafe_werkzeug=True)
