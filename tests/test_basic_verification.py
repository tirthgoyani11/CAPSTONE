import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_dashboard_route(self):
        print("Testing Dashboard Route...")
        response = self.app.get('/')
        # Protected route redirects to login when not authenticated
        self.assertIn(response.status_code, [200, 302], "Dashboard did not return expected status")

    def test_analytics_route(self):
        print("Testing Analytics Route...")
        response = self.app.get('/analytics')
        # Protected route redirects to login when not authenticated
        self.assertIn(response.status_code, [200, 302], "Analytics did not return expected status")

    def test_settings_route(self):
        print("Testing Settings Route...")
        response = self.app.get('/settings')
        # Protected route redirects to login when not authenticated
        self.assertIn(response.status_code, [200, 302], "Settings did not return expected status")

if __name__ == "__main__":
    unittest.main()
