"""
Configuration for Honeypot Module D - Operator Dashboard
Security settings and runtime configuration for the operator interface.
"""
import os

# Database settings
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'events.db')
JSONL_LOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'web_honeypot.jsonl')

# Operator Dashboard settings (Module D)
OPERATOR_PASSWORD = os.environ.get('OPERATOR_PASSWORD', 'honeypot2024!')
OPERATOR_BIND = os.environ.get('OPERATOR_BIND', '127.0.0.1')
OPERATOR_PORT = int(os.environ.get('OPERATOR_PORT', '8090'))
OPERATOR_SESSION_SECRET = os.environ.get('OPERATOR_SESSION_SECRET', 'honeypot-operator-secret-key-2024')

# GeoIP API settings
IPGEOLOCATION_API_KEY = "6910ce5a4c184b44b39803b73fd72bf5"

# Real-time settings
REALTIME_BATCH_INTERVAL = 1  # seconds
MAX_REALTIME_EVENTS = 1000   # max events to keep in memory for streaming

# Security warnings
LAB_USE_ONLY = True
SECURITY_WARNING = "LAB/EDUCATIONAL USE ONLY - DO NOT EXPOSE TO INTERNET"
