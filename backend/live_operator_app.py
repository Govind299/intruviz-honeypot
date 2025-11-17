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
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeypot import storage
from backend.api_tools import get_dashboard_stats, get_map_data

app = Flask(__name__, 
           template_folder='../frontend/operator_templates',
           static_folder='../frontend/operator_static')
app.config['SECRET_KEY'] = 'live-honeypot-super-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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

@app.route('/live/event/<event_id>')
def event_detail(event_id):
    """Event detail page"""
    return render_template('live_event_detail.html', 
                         event_id=event_id,
                         security_warning=SECURITY_WARNING)

# API routes
@app.route('/api/live/events')
def api_live_events():
    """Get events - ONLY after login time by default, but respect user filters"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Get user-provided filters
    user_since = request.args.get('since', '')
    ip_filter = request.args.get('ip', '')
    country_filter = request.args.get('country', '')
    type_filter = request.args.get('type', '')
    
    # Build filters dictionary
    filters = {}
    
    # If user provides a 'since' filter, use it; otherwise default to login time
    if user_since:
        # Check if it's a date-only format (YYYY-MM-DD) and convert to datetime range
        if len(user_since) == 10 and user_since.count('-') == 2:
            # Date only - set range from 00:00:00 to 23:59:59 of that day
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(user_since, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            
            filters['since'] = f"{user_since} 00:00:00"
            filters['until'] = next_day.strftime('%Y-%m-%d %H:%M:%S')
            print(f"📅 User applied date filter: {user_since}")
            print(f"📅 Range: {filters['since']} to {filters['until']}")
        elif 'T' in user_since:
            # ISO format timestamp from time range filter (e.g., "2025-11-16T11:51:58.000Z")
            from datetime import datetime
            # Parse ISO format (UTC) and convert to local time for database comparison
            iso_date = datetime.fromisoformat(user_since.replace('Z', '+00:00'))
            # Convert UTC to local time (database stores in local time ISO format)
            local_date = iso_date.astimezone()
            filters['since'] = local_date.isoformat()
            print(f"⏰ User applied time range filter: {user_since}")
            print(f"⏰ Converted to local time: {filters['since']}")
            print(f"⏰ This should show events FROM {filters['since']} TO NOW")
        else:
            # Already has time component - use as-is (for backward compatibility)
            filters['since'] = user_since
            print(f"📅 User applied datetime filter: {user_since}")
    else:
        login_time = session.get('live_login_time')
        if login_time:
            filters['since'] = login_time
            print(f"🔒 Using default login time filter: {login_time}")
    
    # Add other filters if provided
    if ip_filter:
        filters['ip'] = ip_filter
    if country_filter:
        filters['country'] = country_filter
    if type_filter:
        filters['type'] = type_filter
    
    # Get events with filters
    events = storage.query_recent(
        limit=limit,
        offset=offset,
        filters=filters if filters else None
    )
    
    if events:
        print(f"📊 Returning {len(events)} events with filters: {filters}")
        print(f"📊 First event timestamp: {events[0].get('timestamp')}")
        print(f"📊 Last event timestamp: {events[-1].get('timestamp')}")
    else:
        print(f"📊 No events found with filters: {filters}")
    
    return jsonify({
        'events': events,
        'limit': limit,
        'offset': offset,
        'count': len(events),
        'filters': filters
    })

@app.route('/api/live/stats')
def api_live_stats():
    """Get dashboard statistics - respects same filters as events"""
    # Get user-provided filters (same logic as events endpoint)
    user_since = request.args.get('since', '')
    ip_filter = request.args.get('ip', '')
    country_filter = request.args.get('country', '')
    type_filter = request.args.get('type', '')
    
    # Build filters dictionary
    filters = {}
    since_time = None
    until_time = None
    
    # If user provides a 'since' filter, use it; otherwise default to login time
    if user_since:
        # Check if it's a date-only format (YYYY-MM-DD) and convert to datetime range
        if len(user_since) == 10 and user_since.count('-') == 2:
            # Date only - set range from 00:00:00 to next day 00:00:00
            date_obj = datetime.strptime(user_since, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            
            since_time = f"{user_since} 00:00:00"
            until_time = next_day.strftime('%Y-%m-%d %H:%M:%S')
            filters['since'] = since_time
            filters['until'] = until_time
            print(f"📊 Stats date filter: {user_since} (range: {since_time} to {until_time})")
        elif 'T' in user_since:
            # ISO format timestamp from time range filter
            iso_date = datetime.fromisoformat(user_since.replace('Z', '+00:00'))
            # Convert UTC to local time (database stores in local time ISO format)
            local_date = iso_date.astimezone()
            since_time = local_date.isoformat()
            filters['since'] = since_time
            print(f"📊 Stats time range filter: {user_since}")
            print(f"📊 Converted to local time: {since_time}")
        else:
            # Already has time component
            since_time = user_since
            filters['since'] = since_time
            print(f"📊 Stats datetime filter: {user_since}")
    else:
        # Default to login time
        login_time = session.get('live_login_time')
        if not login_time:
            return jsonify({'error': 'No login time'})
        since_time = login_time
        filters['since'] = since_time
        print(f"📊 Stats using login time: {login_time}")
    
    # Add other filters
    if ip_filter:
        filters['ip'] = ip_filter
    if country_filter:
        filters['country'] = country_filter
    if type_filter:
        filters['type'] = type_filter
    
    # Get stats with the same filters
    stats = get_dashboard_stats(since_hours=24, since_time=since_time, until_time=until_time, filters=filters)
    
    # Add TOTAL count of ALL events in database (regardless of filters)
    conn = sqlite3.connect(storage.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events")
    total_all_events = cursor.fetchone()[0]
    conn.close()
    
    stats['total_all_events'] = total_all_events
    print(f"📊 Total events in database: {total_all_events}")
    print(f"🔍 Stats being sent: {stats}")
    
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

@app.route('/api/live/event/<event_id>')
def api_live_event_detail(event_id):
    """Get detailed event information"""
    # Get event details from storage
    event = storage.get_event_by_id(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Create enrichment status
    enrichment = {
        'geolocation_available': bool(event.get('latitude') and event.get('longitude')),
        'country_detected': bool(event.get('country')),
        'isp_detected': bool(event.get('isp')),
        'user_agent_parsed': bool(event.get('user_agent'))
    }
    
    # Return in the format expected by the frontend
    return jsonify({
        'event': event,
        'enrichment': enrichment
    })

@app.route('/api/live/export/csv')
def api_live_export_csv():
    """Export events to CSV with applied filters"""
    from flask import Response
    import csv
    from io import StringIO
    from datetime import datetime, timedelta
    
    # Get user-provided filters (same as events endpoint)
    user_since = request.args.get('since', '')
    ip_filter = request.args.get('ip', '')
    country_filter = request.args.get('country', '')
    type_filter = request.args.get('type', '')
    
    # Build filters dictionary
    filters = {}
    
    # If user provides a 'since' filter, use it; otherwise default to login time
    if user_since:
        if len(user_since) == 10 and user_since.count('-') == 2:
            # Date only
            date_obj = datetime.strptime(user_since, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            filters['since'] = f"{user_since} 00:00:00"
            filters['until'] = next_day.strftime('%Y-%m-%d %H:%M:%S')
        elif 'T' in user_since:
            # ISO format timestamp from time range filter
            iso_date = datetime.fromisoformat(user_since.replace('Z', '+00:00'))
            # Convert UTC to local time (database stores in local time ISO format)
            local_date = iso_date.astimezone()
            filters['since'] = local_date.isoformat()
        else:
            filters['since'] = user_since
    else:
        # Default to login time
        login_time = session.get('live_login_time')
        if login_time:
            filters['since'] = login_time
    
    # Add other filters
    if ip_filter:
        filters['ip'] = ip_filter
    if country_filter:
        filters['country'] = country_filter
    if type_filter:
        filters['type'] = type_filter
    
    # Get all events with filters (no limit)
    events = storage.query_recent(limit=10000, offset=0, filters=filters if filters else None)
    
    # Create CSV
    si = StringIO()
    fieldnames = ['timestamp', 'client_ip', 'country', 'region', 'city', 'attack_type', 
                  'method', 'endpoint', 'username', 'password', 'isp', 'latitude', 'longitude']
    writer = csv.DictWriter(si, fieldnames=fieldnames, extrasaction='ignore')
    
    writer.writeheader()
    for event in events:
        # Extract form data
        form_data = event.get('form_data', {})
        if isinstance(form_data, str):
            import json
            try:
                form_data = json.loads(form_data)
            except:
                form_data = {}
        
        row = {
            'timestamp': event.get('timestamp', ''),
            'client_ip': event.get('client_ip', ''),
            'country': event.get('country', ''),
            'region': event.get('region', ''),
            'city': event.get('city', ''),
            'attack_type': event.get('attack_type', 'login_attempt'),
            'method': event.get('method', 'POST'),
            'endpoint': event.get('endpoint', '/login'),
            'username': form_data.get('username', ''),
            'password': form_data.get('password', ''),
            'isp': event.get('isp', ''),
            'latitude': event.get('latitude', ''),
            'longitude': event.get('longitude', '')
        }
        writer.writerow(row)
    
    output = si.getvalue()
    si.close()
    
    # Create response with CSV file
    filename = f"honeypot_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

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
