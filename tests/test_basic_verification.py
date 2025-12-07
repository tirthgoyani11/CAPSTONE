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
        self.assertEqual(response.status_code, 200, "Dashboard did not return 200 OK")
        self.assertIn(b'NexGen ATS', response.data, "Dashboard content missing")

    def test_analytics_route(self):
        print("Testing Analytics Route...")
        response = self.app.get('/analytics')
        self.assertEqual(response.status_code, 200, "Analytics did not return 200 OK")

    def test_settings_route(self):
        print("Testing Settings Route...")
        response = self.app.get('/settings')
        self.assertEqual(response.status_code, 200, "Settings did not return 200 OK")

if __name__ == "__main__":
    unittest.main()
