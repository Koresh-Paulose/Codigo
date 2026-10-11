import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

if os.environ.get("VERCEL"):
    db_file = Path("/tmp/protege.db")
    # Copy pre-existing database from repo to /tmp if it exists
    for candidate in [Path.cwd() / "protege.db", Path.cwd() / "backend" / "protege.db"]:
        if candidate.exists() and not db_file.exists():
            shutil.copyfile(candidate, db_file)
            break
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
else:
    engine = create_engine("sqlite:///./protege.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()