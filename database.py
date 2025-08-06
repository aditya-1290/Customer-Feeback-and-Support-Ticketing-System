from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL configuration for deployment
# Use environment variables for flexible deployment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:redhat@localhost:5432/crm_db"
)

# For Docker deployment, use the service name
# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://postgres:redhat@db:5432/crm_db"
# )

# For Render deployment, use the provided DATABASE_URL
# DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
