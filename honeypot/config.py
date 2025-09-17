"""
Configuration settings for the Web Application Honeypot.

This module contains all configurable values for the honeypot server.
Modify these values to customize the honeypot behavior.
"""

import os

# Server Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8080       # Default port

# Logging Configuration
LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "web_honeypot.jsonl")
FORCE_FSYNC = True  # Force filesystem sync after each write for data integrity
MAX_LOG_LINE_BYTES = 1024  # Maximum bytes to capture from request body

# Rate Limiting Configuration (per IP)
RATE_LIMIT_REQUESTS = 100  # Maximum requests per time window
RATE_LIMIT_WINDOW = 300    # Time window in seconds (5 minutes)

# Security Configuration
MAX_BODY_SIZE = 16 * 1024  # Maximum request body size (16KB)
FAKE_SERVER_HEADERS = [
    "Apache/2.4.41 (Ubuntu)",
    "nginx/1.18.0",
    "Microsoft-IIS/10.0",
    "Apache/2.4.54 (Unix)"
]

# Application Configuration
SECRET_KEY = "honeypot-secret-key-for-sessions"
DEBUG = False  # Never enable debug mode in production honeypot

# =====================
# Module B: Log Management & Enrichment
# =====================
# SQLite DB path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "events.db")
# Enable/disable DB write
WRITE_TO_DB = True
# Enable/disable enrichment worker
ENABLE_ENRICHMENT = True
# Path to MaxMind GeoLite2 City DB (download required)
GEOLITE2_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "GeoLite2-City.mmdb")
# HTTP fallback for GeoIP (used if MaxMind DB not available)
GEOIP_HTTP_FALLBACK = "http://ip-api.com/json/{ip}"
# Enrichment cache TTL (days)
ENRICH_CACHE_TTL_DAYS = 7
# Max concurrent enrichment lookups
MAX_ENRICH_CONCURRENCY = 4