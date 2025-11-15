"""
Logger for honeypot events with real-time broadcasting
Handles JSONL file logging and real-time event streaming integration.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

def write_event(event_data: Dict[str, Any], log_file_path: str = None):
    """Write event to JSONL log file and broadcast to operator dashboard"""
    
    # Default log file path
    if not log_file_path:
        honeypot_dir = os.path.dirname(os.path.dirname(__file__))
        log_file_path = os.path.join(honeypot_dir, 'data', 'web_honeypot.jsonl')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    # Write to JSONL file
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data) + '\n')
            f.flush()
        print(f"Event logged to: {log_file_path}")
    except Exception as e:
        print(f"Log write error: {e}")
    
    # Import and broadcast to real-time dashboard (non-blocking)
    try:
        from backend.socket_bridge import broadcast_new_event
        broadcast_new_event(event_data)
    except ImportError:
        # Socket bridge not available (operator dashboard not running)
        pass
    except Exception as e:
        print(f"Real-time broadcast error (non-blocking): {e}")

def read_recent_events(log_file_path: str = None, limit: int = 100) -> list:
    """Read recent events from JSONL log file"""
    
    if not log_file_path:
        honeypot_dir = os.path.dirname(os.path.dirname(__file__))
        log_file_path = os.path.join(honeypot_dir, 'data', 'web_honeypot.jsonl')
    
    events = []
    
    if not os.path.exists(log_file_path):
        return events
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Get last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        for line in recent_lines:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"Log read error: {e}")
    
    return events
