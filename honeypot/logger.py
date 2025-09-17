"""
Thread-safe logging module for the Web Application Honeypot.

This module provides secure, thread-safe logging of all honeypot interactions
to a newline-delimited JSON (JSONL) file.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


from . import config
try:
    from . import storage
except ImportError:
    storage = None
try:
    from . import enrich
except ImportError:
    enrich = None


class HoneypotLogger:
    """
    Thread-safe logger for honeypot events.
    
    All events are written to a JSONL file with proper locking to prevent
    race conditions in multi-threaded Flask applications.
    """
    
    def __init__(self, log_path: str = None):
        """Initialize the logger with specified or default log path."""
        self.log_path = log_path or config.LOG_PATH
        self._lock = threading.Lock()
        
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
        # Initialize the log file if it doesn't exist
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                pass  # Create empty file
    
    def write_event(self, event: Dict[str, Any]) -> None:
        """
        Write a honeypot event to the JSONL log file and optionally to SQLite DB.
        Args:
            event: Dictionary containing event data
        """
        # Enrich event with required metadata
        enriched_event = self._enrich_event(event)
        # Convert to JSON and ensure it's within size limits
        json_line = self._serialize_event(enriched_event)
        # Write atomically with file locking (JSONL)
        with self._lock:
            try:
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(json_line + '\n')
                    if config.FORCE_FSYNC:
                        f.flush()
                        os.fsync(f.fileno())
            except Exception as e:
                print(f"ERROR: Failed to write to honeypot log: {e}", file=__import__('sys').stderr)
        # Optionally write to DB (Module B)
        if getattr(config, 'WRITE_TO_DB', False) and storage is not None:
            try:
                event_id = storage.insert_event(enriched_event)
                # Optionally enqueue for enrichment
                if getattr(config, 'ENABLE_ENRICHMENT', False) and enrich is not None:
                    ip = enriched_event.get('client_ip')
                    if ip:
                        enrich.enqueue_for_enrichment(event_id, ip)
            except Exception as e:
                print(f"ERROR: Failed to write event to DB: {e}", file=__import__('sys').stderr)
    
    def _enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich the event with required metadata fields.
        
        Args:
            event: Base event dictionary
            
        Returns:
            Enriched event with all required fields
        """
        enriched = event.copy()
        
        # Add required fields if not present
        if 'id' not in enriched:
            enriched['id'] = str(uuid.uuid4())
        
        if 'timestamp' not in enriched:
            enriched['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Ensure all required fields exist with defaults
        required_fields = {
            'client_ip': 'unknown',
            'method': 'unknown',
            'endpoint': 'unknown',
            'headers': {},
            'query_params': {},
            'cookies': {},
            'form_data': {},
            'user_agent': 'unknown',
            'raw_body_preview': ''
        }
        
        for field, default_value in required_fields.items():
            if field not in enriched:
                enriched[field] = default_value
        
        return enriched
    
    def _serialize_event(self, event: Dict[str, Any]) -> str:
        """
        Serialize event to JSON with size limits and safety checks.
        
        Args:
            event: Event dictionary to serialize
            
        Returns:
            JSON string representation of the event
        """
        try:
            # Truncate large fields to prevent log file bloat
            if isinstance(event.get('raw_body_preview'), str):
                event['raw_body_preview'] = event['raw_body_preview'][:config.MAX_LOG_LINE_BYTES]
            
            # Convert datetime objects to ISO format strings
            for key, value in event.items():
                if isinstance(value, datetime):
                    event[key] = value.isoformat()
            
            # Serialize to JSON without newlines
            return json.dumps(event, ensure_ascii=False, separators=(',', ':'))
            
        except (TypeError, ValueError) as e:
            # If serialization fails, create a minimal error event
            error_event = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': f'Failed to serialize event: {str(e)}',
                'original_event_keys': list(event.keys()) if isinstance(event, dict) else 'invalid'
            }
            return json.dumps(error_event, ensure_ascii=False, separators=(',', ':'))


# Global logger instance
_logger_instance = None


def get_logger() -> HoneypotLogger:
    """
    Get the global logger instance (singleton pattern).
    
    Returns:
        HoneypotLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = HoneypotLogger()
    return _logger_instance


def write_event(event: Dict[str, Any]) -> None:
    """
    Convenience function to write an event using the global logger.
    
    Args:
        event: Event dictionary to log
    """
    get_logger().write_event(event)