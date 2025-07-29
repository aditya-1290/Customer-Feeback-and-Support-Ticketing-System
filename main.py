from fastapi import FastAPI
from routers import auth, tickets, frontend
from database import engine, Base
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Customer Feedback and Support Ticketing System")

# Create database tables
Base.metadata.create_all(bind=engine)
   
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates directory with absolute path
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(frontend.router)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])

              