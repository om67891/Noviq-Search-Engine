from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Wait until database URL is explicitly defined or default to a local string if needed
# We assume DATABASE_URL is properly formed: postgresql://user:pass@host:port/dbname
engine = create_engine(
    settings.DATABASE_URL or "postgresql://postgres:postgres@localhost:5432/noviq",
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
