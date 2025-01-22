import unittest
import sys
import os
from datetime import datetime

class TestValidation(unittest.TestCase):
    def test_box_id_format(self):
        """Test box ID format validation"""
        valid_box_ids = [
            'ROOM1#BOX001',
            'ROOM2#BOX123',
            'ROOM10#BOX999'
        ]
        
        invalid_box_ids = [
            'ROOM1BOX001',  # Missing #
            'room1#box001',  # Wrong case
            'ROOM#BOX',     # Missing numbers
            'R1#B1'         # Wrong format
        ]
        
        for box_id in valid_box_ids:
            self.assertTrue(self.validate_box_id(box_id))
            
        for box_id in invalid_box_ids:
            self.assertFalse(self.validate_box_id(box_id))

    def test_weight_validation(self):
        """Test weight validation"""
        valid_weights = [0, 50, 100, 999.99]
        invalid_weights = [-1, -50, 1001, 'abc']
        
        for weight in valid_weights:
            self.assertTrue(self.validate_weight(weight))
            
        for weight in invalid_weights:
            self.assertFalse(self.validate_weight(weight))

    def test_customer_data(self):
        """Test customer data validation"""
        valid_customer = {
            'customer_id': 'CUST001',
            'company_name': 'Test Company',
            'email': 'test@example.com'
        }
        
        invalid_customer = {
            'customer_id': 'C1',  # Too short
            'company_name': '',   # Empty
            'email': 'invalid-email'  # Invalid format
        }
        
        self.assertTrue(self.validate_customer_data(valid_customer))
        self.assertFalse(self.validate_customer_data(invalid_customer))

    @staticmethod
    def validate_box_id(box_id):
        import re
        pattern = r'^ROOM[0-9]+#BOX[0-9]{3,}$'
        return bool(re.match(pattern, box_id))

    @staticmethod
    def validate_weight(weight):
        try:
            w = float(weight)
            return 0 <= w <= 1000
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_customer_data(data):
        if not all(key in data for key in ['customer_id', 'company_name', 'email']):
            return False
        
        # Validate customer_id
        if len(data['customer_id']) < 5:
            return False
            
        # Validate company_name
        if not data['company_name'].strip():
            return False
            
        # Validate email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return False
            
        return True

if __name__ == '__main__':
    unittest.main()
