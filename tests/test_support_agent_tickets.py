import unittest
from fastapi.testclient import TestClient
from main import app
from database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models as models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Create the test database schema
Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestSupportAgentTickets(unittest.TestCase):

    def setUp(self):
        # Setup test data in test database
        self.db = next(override_get_db())
        # Clear existing data
        self.db.query(models.TicketResponse).delete()
        self.db.query(models.Ticket).delete()
        self.db.query(models.User).delete()
        self.db.commit()

        # Create test users
        self.support_agent = models.User(email="support_agent@example.com", name="Support Agent", role=models.UserRole.support_agent, password_hash="fakehash")
        self.customer = models.User(email="customer@example.com", name="Customer", role=models.UserRole.customer, password_hash="fakehash")
        self.unauthorized_user = models.User(email="unauthorized_user@example.com", name="Unauthorized", role=models.UserRole.customer, password_hash="fakehash")
        self.db.add_all([self.support_agent, self.customer, self.unauthorized_user])
        self.db.commit()

        # Create test ticket
        self.ticket = models.Ticket(user_id=self.customer.id, subject="Test Ticket", description="Test Description", priority="medium", status=models.TicketStatus.open)
        self.db.add(self.ticket)
        self.db.commit()

    def tearDown(self):
        # Clean up test data
        self.db.query(models.TicketResponse).delete()
        self.db.query(models.Ticket).delete()
        self.db.query(models.User).delete()
        self.db.commit()
        self.db.close()

    def test_get_tickets_support_agent(self):
        response = client.get("/get_tickets", params={"email_query": "support_agent@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_tickets_customer(self):
        response = client.get("/get_tickets", params={"email_query": "customer@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_add_ticket_response_authorized(self):
        data = {
            "message": "Test response",
            "email": "support_agent@example.com"
        }
        response = client.post(f"/add_ticket_response/{self.ticket.id}/responses", data=data)
        self.assertIn(response.status_code, [200, 303])

    def test_add_ticket_response_unauthorized(self):
        data = {
            "message": "Test response",
            "email": "unauthorized_user@example.com"
        }
        response = client.post(f"/add_ticket_response/{self.ticket.id}/responses", data=data)
        self.assertIn(response.status_code, [403, 401])

if __name__ == "__main__":
    unittest.main()
