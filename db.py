from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
Base = declarative_base()



class PRReport(Base):
    __tablename__ = "pr_reports"

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

init_db()