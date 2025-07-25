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
        reg_response = client.post("/login", data={"email": email, "password": password, "role": role, "action": "register"})
        assert reg_response.status_code == 200, f"User registration failed: {reg_response.text}"
        response = client.post("/auth/login", data={"username": email, "password": password})
        assert response.status_code == 200, f"User login failed: {response.text}"
        # Set cookie for user_email for authentication
        client.cookies.set("user_email", email)
        self.headers = {}

        # Register and login a support agent user
        agent_email = "agent@example.com"
        agent_password = "agentpassword"
        agent_role = "support_agent"
        reg_agent_response = client.post("/login", data={"email": agent_email, "password": agent_password, "role": agent_role, "action": "register"})
        assert reg_agent_response.status_code == 200, f"Agent registration failed: {reg_agent_response.text}"
        agent_response = client.post("/auth/login", data={"username": agent_email, "password": agent_password})
        assert agent_response.status_code == 200, f"Agent login failed: {agent_response.text}"
        # Set cookie for user_email for authentication
        client.cookies.set("user_email", agent_email)
        self.agent_headers = {}

    @data(
        {"subject": "Test Ticket 1", "description": "Description 1", "priority": "High"},
        {"subject": "Test Ticket 2", "description": "Description 2", "priority": "Low"},
    )
    def test_create_ticket(self, ticket_data):
        response = client.post("/tickets/create_ticket", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["subject"], ticket_data["subject"])
        self.assertEqual(json_data["description"], ticket_data["description"])
        self.assertEqual(json_data["priority"], ticket_data["priority"])

    def test_get_tickets(self):
        response = client.get("/tickets/get_tickets", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_add_ticket_response_authorized(self):
        # Create a ticket first
        ticket_data = {"subject": "Response Ticket", "description": "Test response", "priority": "Medium"}
        response = client.post("/tickets/create_ticket", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json().get("id")
        self.assertIsNotNone(ticket_id, "Ticket ID not found in create_ticket response")

        # Add response as ticket owner
        response_data = {"message": "This is a response from owner"}
        response = client.post(f"/tickets/add_ticket_response/{ticket_id}/responses", json=response_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], response_data["message"])

        # Add response as support agent
        response_data_agent = {"message": "This is a response from agent"}
        response = client.post(f"/tickets/add_ticket_response/{ticket_id}/responses", json=response_data_agent, headers=self.agent_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], response_data_agent["message"])

    def test_add_ticket_response_unauthorized(self):
        # Create a ticket with one user
        ticket_data = {"subject": "Unauthorized Response Ticket", "description": "Test unauthorized response", "priority": "Low"}
        response = client.post("/tickets/create_ticket", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json().get("id")
        self.assertIsNotNone(ticket_id, "Ticket ID not found in create_ticket response")

        # Register and login another customer
        other_email = "otheruser@example.com"
        other_password = "otherpassword"
        reg_other_response = client.post("/login", data={"email": other_email, "password": other_password, "role": "customer", "action": "register"})
        self.assertEqual(reg_other_response.status_code, 200, f"Other user registration failed: {reg_other_response.text}")
        other_response = client.post("/auth/login", data={"username": other_email, "password": other_password})
        self.assertEqual(other_response.status_code, 200, f"Other user login failed: {other_response.text}")
        other_token = other_response.json().get("access_token")
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to add response as unauthorized user
        response_data = {"message": "Unauthorized response"}
        response = client.post(f"/tickets/add_ticket_response/{ticket_id}/responses", json=response_data, headers=other_headers)
        self.assertEqual(response.status_code, 403)

    def test_update_ticket_status_authorized(self):
        # Create a ticket first
        ticket_data = {"subject": "Status Ticket", "description": "Test status update", "priority": "Low"}
        response = client.post("/tickets/create_ticket", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json().get("id")
        self.assertIsNotNone(ticket_id, "Ticket ID not found in create_ticket response")

        # Update status as support agent
        update_data = {"status": "closed"}
        response = client.patch(f"/tickets/update_ticket_status/{ticket_id}", json=update_data, headers=self.agent_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "closed")

    def test_update_ticket_status_unauthorized(self):
        # Create a ticket first
        ticket_data = {"subject": "Unauthorized Status Ticket", "description": "Test unauthorized status update", "priority": "Low"}
        response = client.post("/tickets/create_ticket", json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        ticket_id = response.json().get("id")
        self.assertIsNotNone(ticket_id, "Ticket ID not found in create_ticket response")

        # Try to update status as customer (unauthorized)
        update_data = {"status": "closed"}
        response = client.patch(f"/tickets/update_ticket_status/{ticket_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 403)
