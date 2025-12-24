from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, JSON
from datetime import datetime
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
import json
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB  # ✅ Use JSONB for Postgres

Base = declarative_base()

class PRMetadata(Base):
    __tablename__ = "pull_requests-test"

    id = Column(Integer, primary_key=True, index=True)
    pr_number = Column(Integer, index=True)
    repo = Column(String, index=True)
    title = Column(String)
    author = Column(String)
    url = Column(String)
    created_at = Column(DateTime)
    
    # ✅ CHANGED: This stores the rich [{"filename": "...", "patch": "..."}] structure
    files = Column(JSONB)
    



class PRReport(Base):
    __tablename__ = "pr_reports-test"

    id = Column(String, primary_key=True)
    pr_id = Column(String)
    report_md = Column(Text)
    file_path = Column(String)

engine = create_engine(settings.DB_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
    
