"""
Web Application Honeypot - Main Flask Application

This module implements a honeypot that simulates a login page to capture
attacker interactions. All requests are logged for analysis.

SECURITY WARNING: This is for LAB/EDUCATIONAL USE ONLY.
Do not expose to the public internet without proper isolation.
"""

import random
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any

from flask import Flask, request, render_template, jsonify, make_response
from markupsafe import escape
from werkzeug.exceptions import RequestEntityTooLarge

from . import config
from . import logger


class RateLimiter:
    """Simple in-memory rate limiter for honeypot protection."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked_ips = defaultdict(datetime)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if the client IP is allowed to make a request."""
        now = datetime.now()
        
        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False
            else:
                # Unblock expired IPs
                del self.blocked_ips[client_ip]
        
        # Clean old requests
        cutoff = now - timedelta(seconds=config.RATE_LIMIT_WINDOW)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= config.RATE_LIMIT_REQUESTS:
            # Block IP for double the rate limit window
            self.blocked_ips[client_ip] = now + timedelta(seconds=config.RATE_LIMIT_WINDOW * 2)
            return False
        
        # Record this request
        self.requests[client_ip].append(now)
        return True


def create_app() -> Flask:
    """
    Create and configure the Flask honeypot application.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_BODY_SIZE
    
    # Initialize rate limiter
    rate_limiter = RateLimiter()
    
    def get_client_ip() -> str:
        """Extract the real client IP from request headers."""
        # Check for forwarded headers (common in proxy setups)
        forwarded_ips = request.headers.get('X-Forwarded-For', '').split(',')
        if forwarded_ips and forwarded_ips[0].strip():
            return forwarded_ips[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def log_request(additional_data: Dict[str, Any] = None) -> None:
        """
        Log the current request with all relevant details.
        
        Args:
            additional_data: Additional data to include in the log
        """
        client_ip = get_client_ip()
        
        # Extract request body preview safely
        raw_body_preview = ''
        if request.data:
            try:
                raw_body_preview = request.data.decode('utf-8', errors='replace')[:config.MAX_LOG_LINE_BYTES]
            except Exception:
                raw_body_preview = '<binary data>'
        
        # Create base event
        event = {
            'client_ip': client_ip,
            'method': request.method,
            'endpoint': request.endpoint or request.path,
            'full_path': request.full_path,
            'headers': dict(request.headers),
            'query_params': dict(request.args),
            'cookies': dict(request.cookies),
            'form_data': dict(request.form) if request.form else {},
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'raw_body_preview': raw_body_preview,
            'content_type': request.content_type,
            'content_length': request.content_length,
            'referrer': request.referrer,
            'remote_addr': request.remote_addr,
            'scheme': request.scheme,
            'is_secure': request.is_secure
        }
        
        # Add any additional data
        if additional_data:
            event.update(additional_data)
        
        # Log the event
        logger.write_event(event)
    
    def add_fake_server_header(response):
        """Add a fake server header to make the honeypot less obvious."""
        fake_server = random.choice(config.FAKE_SERVER_HEADERS)
        response.headers['Server'] = fake_server
        return response
    
    @app.before_request
    def before_request():
        """Check rate limits and log all incoming requests."""
        client_ip = get_client_ip()
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            log_request({'rate_limited': True, 'action': 'blocked'})
            return jsonify({'error': 'Too many requests'}), 429
    
    @app.after_request
    def after_request(response):
        """Add security headers and fake server info."""
        return add_fake_server_header(response)
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_request(e):
        """Handle requests that are too large."""
        log_request({'error': 'request_too_large', 'action': 'rejected'})
        return jsonify({'error': 'Request too large'}), 413
    
    @app.route('/login', methods=['GET'])
    def login_get():
        """
        Serve the fake login page.
        
        Returns:
            Rendered HTML login form
        """
        log_request({'action': 'serve_login_page'})
        return render_template('login.html')
    
    @app.route('/login', methods=['POST'])
    def login_post():
        """
        Handle login form submissions.
        
        This endpoint captures all submitted data and always returns
        a failure message to prevent any real authentication.
        
        Returns:
            Rendered HTML login form with error message
        """
        # Extract submitted credentials and other form data
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Log the login attempt with captured credentials
        log_request({
            'action': 'login_attempt',
            'username': username,
            'password': password,
            'credentials_captured': True,
            'form_fields': list(request.form.keys())
        })
        
        # Always return failure - never authenticate
        # Sanitize the error message to prevent XSS in case of reflected errors
        error_message = "Invalid username or password. Please try again."
        
        # Add small delay to simulate real authentication check
        time.sleep(random.uniform(0.5, 1.5))
        
        # Use escape() to sanitize any user input that might be reflected
        # (though in this case we're using a static message)
        safe_error_message = escape(error_message)
        
        return render_template('login.html', error=safe_error_message)
    
    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon requests to avoid 404s in logs."""
        log_request({'action': 'favicon_request'})
        return '', 204
    
    @app.route('/')
    def index():
        """Redirect root requests to login page."""
        log_request({'action': 'root_access'})
        return render_template('login.html')
    
    @app.route('/<path:path>')
    def catch_all(path):
        """
        Catch all other requests and log them.
        
        Args:
            path: The requested path
            
        Returns:
            404 error response
        """
        log_request({
            'action': 'unknown_path_access',
            'requested_path': path,
            'potential_scan': True
        })
        return jsonify({'error': 'Not found'}), 404
    
    return app


def main():
    """
    Main entry point for the honeypot application.
    
    Displays security warnings and starts the Flask development server.
    """
    print("=" * 60)
    print("🍯 WEB APPLICATION HONEYPOT - STARTING")
    print("=" * 60)
    print()
    print("⚠️  SECURITY WARNING:")
    print("   This honeypot is for LAB/EDUCATIONAL USE ONLY!")
    print("   Do not expose to the public internet without proper isolation.")
    print("   Use only in controlled environments (VM, isolated VLAN).")
    print()
    print(f"📊 Configuration:")
    print(f"   - Server: {config.HOST}:{config.PORT}")
    print(f"   - Log file: {config.LOG_PATH}")
    print(f"   - Rate limit: {config.RATE_LIMIT_REQUESTS} req/{config.RATE_LIMIT_WINDOW}s")
    print()
    print("🎯 Target endpoints:")
    print("   - GET  /login  (serves fake login page)")
    print("   - POST /login  (captures credentials)")
    print()
    print("📝 All interactions will be logged to JSONL format")
    print("=" * 60)
    print()
    
    # Create the Flask app
    app = create_app()
    
    # Start the server
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            threaded=True  # Enable threading for concurrent requests
        )
    except KeyboardInterrupt:
        print("\n🛑 Honeypot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting honeypot: {e}")


if __name__ == "__main__":
    main()