# Local Development Setup Guide

## Problem Fixed
The error `could not translate host name "db" to address: Name or service not known` was caused by:
1. Docker daemon not running on Windows
2. Database connection string pointing to Docker hostname "db"
3. Inconsistent PostgreSQL configuration

## Quick Fix for Local Development

### Option 1: Use SQLite (Recommended for Quick Start)
1. **No additional setup required** - SQLite is included with Python
2. **Database file**: `test.db` will be created automatically
3. **Connection string**: Already configured in `.env`

### Option 2: Use Local PostgreSQL (Advanced)
1. **Install PostgreSQL**:
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, set password to `redhat`
   - Create database: `crm_db`

2. **Update .env file**:
   ```
   DATABASE_URL=postgresql://postgres:redhat@localhost:5432/crm_db
   USE_SQLITE=false
   ```

3. **Start PostgreSQL service**:
   - Windows: `net start postgresql-x64-17`
   - Or use PostgreSQL service manager

## Running the Application

### For SQLite (Quick Start):
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m CRM.main
```

### For PostgreSQL:
```bash
# Ensure PostgreSQL is running
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m CRM.main
```

## Testing the Database Connection

```python
# Test script
from CRM.database import engine
try:
    with engine.connect() as conn:
        print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

## Docker Setup (When Ready)

### Prerequisites:
1. **Install Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. **Start Docker Desktop** (ensure it's running)

### Run with Docker:
```bash
# Build and start services
docker-compose up --build

# Access application
# http://localhost:10000
```

## Troubleshooting

### Common Issues:
1. **"psycopg2 not found"**: Install with `pip install psycopg2-binary`
2. **"Port 5432 already in use"**: Change port in docker-compose.yml
3. **"Permission denied"**: Run terminal as administrator on Windows

### Database Reset:
```bash
# For SQLite
rm test.db

# For PostgreSQL
psql -U postgres -c "DROP DATABASE crm_db;"
psql -U postgres -c "CREATE DATABASE crm_db;"
```

## Environment Variables Summary

| Variable | SQLite Value | PostgreSQL Value |
|----------|--------------|------------------|
| DATABASE_URL | sqlite:///./test.db | postgresql://postgres:redhat@localhost:5432/crm_db |
| USE_SQLITE | true | false |
| DEBUG | true | true |
