"""
SQLite storage and query API for honeypot events (Module B).
Handles DB schema, event insertion, enrichment updates, and queries.
"""
import os
import sqlite3
import threading
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from . import config

_DB_LOCK = threading.Lock()


def get_db_conn(db_path: Optional[str] = None):
    """Get a SQLite connection (thread-safe)."""
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    """Create DB and tables if not exist (idempotent)."""
    path = db_path or config.DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _DB_LOCK:
        conn = get_db_conn(path)
        cur = conn.cursor()
        # Main events table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            client_ip TEXT,
            method TEXT,
            endpoint TEXT,
            headers TEXT,
            query_params TEXT,
            cookies TEXT,
            form_data TEXT,
            user_agent TEXT,
            raw_body_preview TEXT,
            raw_json TEXT,
            enriched INTEGER DEFAULT 0,
            country TEXT,
            region TEXT,
            city TEXT,
            asn TEXT,
            isp TEXT,
            rdns TEXT
        );''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_ts ON events(timestamp);')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_ip ON events(client_ip);')
        # Geo cache table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS geo_cache (
            ip TEXT PRIMARY KEY,
            country TEXT,
            region TEXT,
            city TEXT,
            asn TEXT,
            isp TEXT,
            rdns TEXT,
            last_seen TEXT
        );''')
        conn.commit()
        conn.close()


def insert_event(raw_event: Dict[str, Any], db_path: Optional[str] = None) -> str:
    """
    Insert a normalized event into the DB. Returns event UUID.
    """
    from uuid import uuid4
    event = dict(raw_event)  # Copy
    event_id = event.get('id') or str(uuid4())
    event['id'] = event_id
    event['timestamp'] = event.get('timestamp') or datetime.utcnow().isoformat()
    # Serialize JSON fields
    def safe_json(val):
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return '{}'
    headers = safe_json(event.get('headers', {}))
    query_params = safe_json(event.get('query_params', {}))
    cookies = safe_json(event.get('cookies', {}))
    form_data = safe_json(event.get('form_data', {}))
    raw_json = safe_json(event)
    with _DB_LOCK:
        conn = get_db_conn(db_path)
        cur = conn.cursor()
        cur.execute('''
            INSERT OR IGNORE INTO events (
                id, timestamp, client_ip, method, endpoint, headers, query_params, cookies, form_data, user_agent, raw_body_preview, raw_json, enriched
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            event_id,
            event['timestamp'],
            event.get('client_ip'),
            event.get('method'),
            event.get('endpoint'),
            headers,
            query_params,
            cookies,
            form_data,
            event.get('user_agent'),
            event.get('raw_body_preview'),
            raw_json
        ))
        conn.commit()
        conn.close()
    return event_id


def update_enrichment(event_id: str, enrichment: Dict[str, Any], db_path: Optional[str] = None):
    """
    Update enrichment fields for an event (country, city, asn, etc.).
    """
    with _DB_LOCK:
        conn = get_db_conn(db_path)
        cur = conn.cursor()
        cur.execute('''
            UPDATE events SET
                country = ?,
                region = ?,
                city = ?,
                asn = ?,
                isp = ?,
                rdns = ?,
                enriched = 1
            WHERE id = ?
        ''', (
            enrichment.get('country'),
            enrichment.get('region'),
            enrichment.get('city'),
            enrichment.get('asn'),
            enrichment.get('isp'),
            enrichment.get('rdns'),
            event_id
        ))
        conn.commit()
        conn.close()


def query_recent(limit: int = 100, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return the most recent N events (as dicts).
    """
    with _DB_LOCK:
        conn = get_db_conn(db_path)
        cur = conn.cursor()
        cur.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        conn.close()
    return [dict(row) for row in rows]


def query_top_ips(limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return top IPs by event count.
    """
    with _DB_LOCK:
        conn = get_db_conn(db_path)
        cur = conn.cursor()
        cur.execute('''
            SELECT client_ip, COUNT(*) as count
            FROM events
            GROUP BY client_ip
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        rows = cur.fetchall()
        conn.close()
    return [dict(row) for row in rows]


def query_failed_logins_per_hour(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return failed login attempts per hour (UTC).
    """
    with _DB_LOCK:
        conn = get_db_conn(db_path)
        cur = conn.cursor()
        cur.execute('''
            SELECT substr(timestamp, 1, 13) as hour, COUNT(*) as count
            FROM events
            WHERE endpoint = '/login' AND method = 'POST'
            GROUP BY hour
            ORDER BY hour DESC
        ''')
        rows = cur.fetchall()
        conn.close()
    return [dict(row) for row in rows]


# Initialize DB on import (safe to call multiple times)
init_db()
