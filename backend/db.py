import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Search for .env and .env.local
for env_path in [
    Path.cwd() / ".env.local",
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env.local",
    Path.cwd() / "backend" / ".env",
    Path(__file__).resolve().parents[1] / ".env.local",
    Path(__file__).resolve().parents[1] / ".env"
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("NEON_DATABASE_URL")

if db_url and db_url.strip():
    db_url = db_url.strip()
    # Normalize to postgresql+psycopg2:// for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Configure resilient engine for Neon serverless Postgres
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    is_postgres = True
elif os.environ.get("VERCEL"):
    db_file = Path("/tmp/protege.db")
    for candidate in [Path.cwd() / "protege.db", Path.cwd() / "backend" / "protege.db"]:
        if candidate.exists() and not db_file.exists():
            shutil.copyfile(candidate, db_file)
            break
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    is_postgres = False
else:
    engine = create_engine("sqlite:///./protege.db", connect_args={"check_same_thread": False})
    is_postgres = False

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()