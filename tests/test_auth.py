import unittest
from ddt import ddt, data, unpack
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@ddt
class TestAuth(unittest.TestCase):

    @data(
        ("nonexistent@example.com", "wrongpassword"),
        ("", ""),
    )
    @unpack
    def test_login_failures(self, email, password):
        response = client.post("/auth/login", data={"username": email, "password": password})
        self.assertEqual(response.status_code, 401)

    def test_register_and_login(self):
        # Register a new user
        email = "testuser@example.com"
        password = "testpassword"
        role = "customer"
        response = client.post("/auth/login", data={"username": email, "password": password})
        self.assertEqual(response.status_code, 401)  # User does not exist yet

        # Register user via frontend registration (simulate)
        response = client.post("/login", data={"email": email, "password": password, "role": role, "action": "register"})
        self.assertEqual(response.status_code, 200)

        # Login with correct credentials
        response = client.post("/auth/login", data={"username": email, "password": password})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("access_token", json_data)
        self.assertEqual(json_data["token_type"], "bearer")

    def test_login_wrong_role(self):
        # Register user as customer
        email = "roleuser@example.com"
        password = "testpassword"
        role = "customer"
        client.post("/login", data={"email": email, "password": password, "role": role, "action": "register"})

        # Try login with wrong role
        response = client.post("/auth/login", data={"username": email, "password": password})
        self.assertEqual(response.status_code, 200)  # Login endpoint does not check role

        # Frontend login with wrong role should fail
        response = client.post("/login", data={"email": email, "password": password, "role": "support_agent", "action": "login"})
        self.assertIn("Invalid credentials", response.text)
