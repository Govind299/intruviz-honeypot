#!/usr/bin/env python3
"""
Honeypot Test Simulation Script

This script tests the web honeypot by simulating various types of attacks
and legitimate login attempts. It verifies that events are properly logged
and the honeypot responds appropriately.

Usage:
    python -m honeypot.tests.test_simulate
    
Or with custom target:
    python -m honeypot.tests.test_simulate --host 127.0.0.1 --port 8080
"""

import argparse
import json
import os
import requests
import sys
import time
from typing import List, Dict, Any
from urllib.parse import urljoin


class HoneypotTester:
    """Test suite for the web application honeypot."""
    
    def __init__(self, base_url: str, log_path: str = None):
        """
        Initialize the tester.
        
        Args:
            base_url: Base URL of the honeypot (e.g., http://127.0.0.1:8080)
            log_path: Path to the honeypot log file for verification
        """
        self.base_url = base_url.rstrip('/')
        self.log_path = log_path
        self.session = requests.Session()
        
        # Test payloads for different attack types
        self.test_payloads = {
            'sql_injection': [
                ("admin", "' OR '1'='1"),
                ("admin", "admin'; DROP TABLE users; --"),
                ("admin", "1' UNION SELECT * FROM users --"),
                ("' OR 1=1 --", "password")
            ],
            'xss_attempts': [
                ("<script>alert('XSS')</script>", "password"),
                ("admin", "<img src=x onerror=alert('XSS')>"),
                ("javascript:alert('XSS')", "password")
            ],
            'credential_stuffing': [
                ("admin", "admin"),
                ("admin", "password"),
                ("admin", "123456"),
                ("root", "root"),
                ("user", "user"),
                ("test", "test")
            ],
            'legitimate_attempts': [
                ("john.doe", "MySecurePassword123!"),
                ("alice.smith", "AliceP@ssw0rd2023"),
                ("bob.johnson", "BobSecure987#")
            ]
        }
    
    def run_all_tests(self) -> bool:
        """
        Run all test scenarios.
        
        Returns:
            True if all tests pass, False otherwise
        """
        print("🧪 Starting Honeypot Test Suite")
        print("=" * 50)
        
        test_results = []
        
        # Test basic connectivity
        test_results.append(self._test_connectivity())
        
        # Test GET request to login page
        test_results.append(self._test_login_page_get())
        
        # Test various attack scenarios
        for attack_type, payloads in self.test_payloads.items():
            print(f"\n🎯 Testing {attack_type.replace('_', ' ').title()}")
            test_results.append(self._test_attack_scenario(attack_type, payloads))
        
        # Test rate limiting
        test_results.append(self._test_rate_limiting())
        
        # Test malformed requests
        test_results.append(self._test_malformed_requests())
        
        # Verify log entries if log path is provided
        if self.log_path:
            test_results.append(self._test_log_verification())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All tests PASSED!")
            return True
        else:
            print("❌ Some tests FAILED!")
            return False
    
    def _test_connectivity(self) -> bool:
        """Test basic connectivity to the honeypot."""
        print("🌐 Testing connectivity...")
        try:
            response = self.session.get(self.base_url, timeout=5)
            if response.status_code == 200:
                print("   ✅ Connectivity: PASS")
                return True
            else:
                print(f"   ❌ Connectivity: FAIL (status {response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ Connectivity: FAIL ({e})")
            return False
    
    def _test_login_page_get(self) -> bool:
        """Test GET request to login page."""
        print("📄 Testing login page GET request...")
        try:
            response = self.session.get(urljoin(self.base_url, '/login'), timeout=5)
            
            if response.status_code != 200:
                print(f"   ❌ Login page GET: FAIL (status {response.status_code})")
                return False
            
            # Check if response contains expected HTML elements
            content = response.text.lower()
            required_elements = ['username', 'password', 'form', 'login']
            
            for element in required_elements:
                if element not in content:
                    print(f"   ❌ Login page GET: FAIL (missing {element})")
                    return False
            
            print("   ✅ Login page GET: PASS")
            return True
            
        except Exception as e:
            print(f"   ❌ Login page GET: FAIL ({e})")
            return False
    
    def _test_attack_scenario(self, attack_type: str, payloads: List[tuple]) -> bool:
        """
        Test a specific attack scenario with multiple payloads.
        
        Args:
            attack_type: Type of attack being tested
            payloads: List of (username, password) tuples to test
            
        Returns:
            True if all payloads are handled correctly
        """
        failed_tests = 0
        
        for i, (username, password) in enumerate(payloads, 1):
            try:
                # Add delay to avoid rate limiting during tests
                time.sleep(0.5)
                
                data = {
                    'username': username,
                    'password': password
                }
                
                response = self.session.post(
                    urljoin(self.base_url, '/login'),
                    data=data,
                    timeout=10
                )
                
                # Honeypot should always return login form with error
                if response.status_code != 200:
                    print(f"   ❌ {attack_type} #{i}: FAIL (status {response.status_code})")
                    failed_tests += 1
                    continue
                
                # Check that no actual authentication occurred
                if 'invalid username or password' not in response.text.lower():
                    print(f"   ❌ {attack_type} #{i}: FAIL (unexpected response)")
                    failed_tests += 1
                    continue
                
                print(f"   ✅ {attack_type} #{i}: PASS")
                
            except Exception as e:
                print(f"   ❌ {attack_type} #{i}: FAIL ({e})")
                failed_tests += 1
        
        success_rate = (len(payloads) - failed_tests) / len(payloads)
        print(f"   📊 {attack_type}: {success_rate:.1%} success rate")
        
        return failed_tests == 0
    
    def _test_rate_limiting(self) -> bool:
        """Test rate limiting functionality."""
        print("⏱️  Testing rate limiting...")
        
        try:
            # Make rapid requests to trigger rate limiting
            responses = []
            for i in range(10):
                response = self.session.post(
                    urljoin(self.base_url, '/login'),
                    data={'username': f'test{i}', 'password': 'test'},
                    timeout=5
                )
                responses.append(response.status_code)
            
            # At least some requests should succeed
            if all(code != 200 for code in responses):
                print("   ❌ Rate limiting: FAIL (no requests succeeded)")
                return False
            
            print("   ✅ Rate limiting: PASS")
            return True
            
        except Exception as e:
            print(f"   ❌ Rate limiting: FAIL ({e})")
            return False
    
    def _test_malformed_requests(self) -> bool:
        """Test handling of malformed requests."""
        print("🔧 Testing malformed requests...")
        
        test_cases = [
            # Empty POST data
            {},
            # Missing username
            {'password': 'test'},
            # Missing password  
            {'username': 'test'},
            # Very long inputs
            {'username': 'x' * 1000, 'password': 'x' * 1000},
            # Special characters
            {'username': '𝕌𝕟𝕚𝕔𝕠𝕕𝕖', 'password': '🔒🗝️'},
        ]
        
        failed_tests = 0
        
        for i, data in enumerate(test_cases, 1):
            try:
                response = self.session.post(
                    urljoin(self.base_url, '/login'),
                    data=data,
                    timeout=5
                )
                
                # Should handle gracefully (200 or 400-level error)
                if response.status_code not in [200, 400, 413, 422]:
                    print(f"   ❌ Malformed request #{i}: FAIL (status {response.status_code})")
                    failed_tests += 1
                else:
                    print(f"   ✅ Malformed request #{i}: PASS")
                
                time.sleep(0.2)  # Small delay
                
            except Exception as e:
                print(f"   ❌ Malformed request #{i}: FAIL ({e})")
                failed_tests += 1
        
        return failed_tests == 0
    
    def _test_log_verification(self) -> bool:
        """Verify that events are being logged correctly."""
        print("📝 Testing log file verification...")
        
        if not os.path.exists(self.log_path):
            print(f"   ❌ Log verification: FAIL (log file not found: {self.log_path})")
            return False
        
        try:
            # Count log entries
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) == 0:
                print("   ❌ Log verification: FAIL (no log entries found)")
                return False
            
            # Verify last few entries are valid JSON
            valid_entries = 0
            for line in lines[-5:]:  # Check last 5 entries
                try:
                    event = json.loads(line.strip())
                    
                    # Check required fields
                    required_fields = ['id', 'timestamp', 'client_ip', 'method', 'endpoint']
                    if all(field in event for field in required_fields):
                        valid_entries += 1
                except json.JSONDecodeError:
                    continue
            
            if valid_entries == 0:
                print("   ❌ Log verification: FAIL (no valid JSON entries)")
                return False
            
            print(f"   ✅ Log verification: PASS ({len(lines)} total entries, {valid_entries} recent valid entries)")
            return True
            
        except Exception as e:
            print(f"   ❌ Log verification: FAIL ({e})")
            return False


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description='Test the Web Application Honeypot')
    parser.add_argument('--host', default='127.0.0.1', help='Honeypot host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Honeypot port (default: 8080)')
    parser.add_argument('--log-path', help='Path to honeypot log file for verification')
    
    args = parser.parse_args()
    
    # Construct base URL
    base_url = f"http://{args.host}:{args.port}"
    
    # Default log path if not specified
    log_path = args.log_path
    if not log_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        honeypot_dir = os.path.dirname(script_dir)
        log_path = os.path.join(honeypot_dir, 'data', 'web_honeypot.jsonl')
    
    print(f"Testing honeypot at: {base_url}")
    print(f"Log file: {log_path}")
    print()
    
    # Run tests
    tester = HoneypotTester(base_url, log_path)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()