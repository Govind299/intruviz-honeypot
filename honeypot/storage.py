"""
Storage layer for honeypot events - SQLite database operations
Provides structured query interface for operator dashboard analytics.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .config import DATABASE_PATH

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create events table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            method TEXT,
            endpoint TEXT,
            headers TEXT,
            form_data TEXT,
            user_agent TEXT,
            raw_json TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            isp TEXT,
            enriched INTEGER DEFAULT 0,
            attack_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_ip ON events(client_ip)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON events(country)")
    # cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON events(created_at)") # Column doesn't exist in current schema
    
    conn.commit()
    conn.close()

def insert_event(event_data: Dict[str, Any]) -> str:
    """Insert a new event into the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    event_id = event_data.get('id', '')
    cursor.execute("""
        INSERT OR REPLACE INTO events (
            id, timestamp, client_ip, method, endpoint, headers, form_data,
            user_agent, raw_json, country, region, city, isp, enriched
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        event_data.get('timestamp', ''),
        event_data.get('ip_address', ''),
        event_data.get('method', 'POST'),
        event_data.get('endpoint', '/login'),
        json.dumps(event_data.get('headers', {})),
        json.dumps(event_data.get('form_data', {})),
        event_data.get('user_agent', ''),
        json.dumps(event_data),
        event_data.get('country', ''),
        event_data.get('region', ''),
        event_data.get('city', ''),
        event_data.get('isp', ''),
        1 if event_data.get('country') else 0
    ))
    
    conn.commit()
    conn.close()
    return event_id

def query_recent(limit: int = 100, offset: int = 0, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Query recent events with optional filters"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if attack_type column exists
    cursor.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in cursor.fetchall()]
    has_attack_type = 'attack_type' in columns
    
    where_clauses = []
    params = []
    
    if filters:
        if filters.get('since'):
            where_clauses.append("timestamp >= ?")
            params.append(filters['since'])
        if filters.get('until'):
            where_clauses.append("timestamp < ?")
            params.append(filters['until'])
        if filters.get('ip'):
            where_clauses.append("client_ip LIKE ?")
            params.append(f"%{filters['ip']}%")
        if filters.get('country'):
            where_clauses.append("country = ?")
            params.append(filters['country'])
        if filters.get('type') and has_attack_type:
            where_clauses.append("attack_type = ?")
            params.append(filters['type'])
    
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    cursor.execute(f"""
        SELECT * FROM events 
        {where_sql}
        ORDER BY timestamp DESC 
        LIMIT ? OFFSET ?
    """, params + [limit, offset])
    
    events = []
    for row in cursor.fetchall():
        event = dict(row)
        # Parse JSON fields
        try:
            event['headers'] = json.loads(event['headers']) if event['headers'] else {}
            event['form_data'] = json.loads(event['form_data']) if event['form_data'] else {}
            event['raw_json'] = json.loads(event['raw_json']) if event['raw_json'] else {}
        except json.JSONDecodeError:
            pass
        events.append(event)
    
    conn.close()
    return events

def query_top_ips(limit: int = 10, since: str = None, until: str = None) -> List[Dict[str, Any]]:
    """Query top attacking IP addresses"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if since:
        where_clauses.append("timestamp >= ?")
        params.append(since)
    if until:
        where_clauses.append("timestamp < ?")
        params.append(until)
    
    where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    cursor.execute(f"""
        SELECT client_ip, COUNT(*) as cnt, MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
        FROM events
        {where_clause}
        GROUP BY client_ip
        ORDER BY cnt DESC
        LIMIT ?
    """, params + [limit])
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'ip': row[0],
            'count': row[1],
            'first_seen': row[2],
            'last_seen': row[3]
        })
    
    conn.close()
    return results

def query_top_countries(limit: int = 10, since: str = None, until: str = None) -> List[Dict[str, Any]]:
    """Query top attacking countries"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if since:
        where_clauses.append("timestamp >= ?")
        params.append(since)
    if until:
        where_clauses.append("timestamp < ?")
        params.append(until)
    
    # Always filter out null/empty countries
    where_clauses.append("country IS NOT NULL AND country != ''")
    
    where_clause = " WHERE " + " AND ".join(where_clauses)
    
    cursor.execute(f"""
        SELECT country, COUNT(*) as cnt
        FROM events
        {where_clause}
        GROUP BY country
        ORDER BY cnt DESC
        LIMIT ?
    """, params + [limit])
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'country': row[0],
            'count': row[1]
        })
    
    conn.close()
    return results

def query_stats_by_time(bucket: str = 'minute', since: str = None, until: str = None) -> List[Dict[str, Any]]:
    """Query event statistics grouped by time bucket"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if bucket == 'minute':
        time_format = '%Y-%m-%dT%H:%M:00'
    elif bucket == 'hour':
        time_format = '%Y-%m-%dT%H:00:00'
    else:
        time_format = '%Y-%m-%d'
    
    where_clauses = []
    params = []
    
    if since:
        where_clauses.append("timestamp >= ?")
        params.append(since)
    if until:
        where_clauses.append("timestamp < ?")
        params.append(until)
    
    where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    cursor.execute(f"""
        SELECT strftime('{time_format}', timestamp) as t, COUNT(*) as cnt
        FROM events
        {where_clause}
        GROUP BY t
        ORDER BY t ASC
    """, params)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'time': row[0],
            'count': row[1]
        })
    
    conn.close()
    return results

def query_map_points(limit: int = 1000, since: str = None) -> List[Dict[str, Any]]:
    """Query geolocated events for map visualization"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if latitude/longitude columns exist
    cursor.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in cursor.fetchall()]
    
    has_coordinates = 'latitude' in columns and 'longitude' in columns
    
    if not has_coordinates:
        print("Warning: latitude/longitude columns not found. Run migrate_database.py first.")
        conn.close()
        return []
    
    since_clause = ""
    params = []
    if since:
        since_clause = "WHERE timestamp >= ?"
        params.append(since)
    
    # Add coordinate filters
    coord_clause = "latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0"
    if since_clause:
        coord_clause = " AND " + coord_clause
    else:
        coord_clause = "WHERE " + coord_clause
    
    cursor.execute(f"""
        SELECT client_ip, country, city, latitude, longitude, 
               MIN(timestamp) as first_seen, MAX(timestamp) as last_seen, COUNT(*) as cnt
        FROM events
        {since_clause}{coord_clause}
        GROUP BY client_ip
        ORDER BY cnt DESC
        LIMIT ?
    """, params + [limit])
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'ip': row[0],
            'country': row[1] or 'Unknown',
            'city': row[2] or 'Unknown',
            'lat': float(row[3]) if row[3] else 0.0,
            'lon': float(row[4]) if row[4] else 0.0,
            'first_seen': row[5],
            'last_seen': row[6],
            'count': row[7]
        })
    
    conn.close()
    return results

def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    """Get a single event by ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    
    if row:
        event = dict(row)
        try:
            event['headers'] = json.loads(event['headers']) if event['headers'] else {}
            event['form_data'] = json.loads(event['form_data']) if event['form_data'] else {}
            event['raw_json'] = json.loads(event['raw_json']) if event['raw_json'] else {}
        except json.JSONDecodeError:
            pass
        conn.close()
        return event
    
    conn.close()
    return None

# Initialize database on import
init_database()
