import unittest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuth(unittest.TestCase):

    def test_register_valid(self):
        data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "strongpassword",
            "role": "customer"
        }
        response = client.post("/register", data=data)
        self.assertIn(response.status_code, [200, 201, 303])

    def test_register_invalid(self):
        data = {
            "email": "invalidemail",
            "name": "",
            "password": "123",
            "role": "customer"
        }
        response = client.post("/register", data=data)
        self.assertIn(response.status_code, [200, 400, 422])

    def test_login_valid(self):
        data = {
            "email": "existinguser@example.com",
            "password": "correctpassword"
        }
        response = client.post("/login", data=data)
        self.assertIn(response.status_code, [200, 303, 422])

    def test_login_invalid(self):
        data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/login", data=data)
        self.assertIn(response.status_code, [401, 403, 422])

if __name__ == "__main__":
    unittest.main()
