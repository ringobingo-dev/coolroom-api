import unittest
import requests
import json
import os
import uuid
from datetime import datetime

class TestCoolRoomAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('config/dev.json') as f:
            cls.config = json.load(f)
        cls.api_url = cls.config.get('ApiUrl')
        cls.test_customer_id = f'TEST{uuid.uuid4().hex[:8]}'

    def test_01_create_user(self):
        """Test user creation and retrieval"""
        # Create user
        user_data = {
            'customer_id': self.test_customer_id,
            'company_name': 'Test Company',
            'email': f'test_{self.test_customer_id}@example.com'
        }
        response = requests.post(f"{self.api_url}/user", json=user_data)
        self.assertEqual(response.status_code, 201)

        # Get user
        response = requests.get(f"{self.api_url}/user/{self.test_customer_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['customer_id'], self.test_customer_id)

    def test_02_box_operations(self):
        """Test box creation and updates"""
        # Create box
        box_data = {
            'customer_id': self.test_customer_id,
            'room_id#box_id': 'ROOM1#BOX001',
            'action': 'IN',
            'weight': 50,
            'variety': 'Potato',
            'temperature': 5
        }
        response = requests.post(f"{self.api_url}/box", json=box_data)
        self.assertEqual(response.status_code, 201)

        # Update box
        update_data = {
            'action': 'UPDATE',
            'weight': 48,
            'temperature': 6
        }
        response = requests.put(
            f"{self.api_url}/box/{self.test_customer_id}/ROOM1#BOX001",
            json=update_data
        )
        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        """Cleanup test data"""
        if hasattr(cls, 'test_customer_id'):
            requests.delete(f"{cls.api_url}/user/{cls.test_customer_id}")

if __name__ == '__main__':
    unittest.main()
