import unittest
from ddt import ddt, data, unpack
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@ddt
class TestTickets(unittest.TestCase):

    def setUp(self):
        # Register and login a test user to get token
        email = "ticketuser@example.com"
        password = "testpassword"
        role = "customer"
        client.post("/login", data={"email": email, "password": password, "role": role, "action": "register"})
        response = client.post("/auth/login", data={"username": email, "password": password})
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @data(
        {"subject": "Test Ticket 1", "description": "Description 1", "priority": "High"},
        {"subject": "Test Ticket 2", "description": "Description 2", "priority": "Low"},
    )
    def test_create_ticket(self, ticket_data):
        response = client.post("/tickets/", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["subject"], ticket_data["subject"])
        self.assertEqual(json_data["description"], ticket_data["description"])
        self.assertEqual(json_data["priority"], ticket_data["priority"])

    def test_get_tickets(self):
        response = client.get("/tickets/", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_add_ticket_response(self):
        # Create a ticket first
        ticket_data = {"subject": "Response Ticket", "description": "Test response", "priority": "Medium"}
        response = client.post("/tickets/", json=ticket_data, headers=self.headers)
        ticket_id = response.json()["id"]

        # Add response
        response_data = {"message": "This is a response"}
        response = client.post(f"/tickets/{ticket_id}/responses", json=response_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], response_data["message"])

    def test_update_ticket_status(self):
        # Create a ticket first
        ticket_data = {"subject": "Status Ticket", "description": "Test status update", "priority": "Low"}
        response = client.post("/tickets/", json=ticket_data, headers=self.headers)
        ticket_id = response.json()["id"]

        # Update status
        update_data = {"status": "closed"}
        response = client.patch(f"/tickets/{ticket_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "closed")
