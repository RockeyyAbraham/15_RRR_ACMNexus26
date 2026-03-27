from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

Base = declarative_base()

class ProtectedContent(Base):
    """Reference content that we are protecting."""
    __tablename__ = "protected_content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_hashes = Column(JSON)  # List of hashes for matching
    content_metadata = Column(JSON)  # Additional content details (Owner, Rights, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    detections = relationship("DetectionEvent", back_populates="content")

class DetectionEvent(Base):
    """A specific instance of piracy detection."""
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("protected_content.id"))
    platform = Column(String, index=True)
    stream_url = Column(String)
    confidence_score = Column(Float)
    consistency_ratio = Column(Float)
    temporal_location = Column(JSON)  # {start: int, end: int}
    ai_summary = Column(String)
    dmca_notice = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content = relationship("ProtectedContent", back_populates="detections")

# Setup Database Engines
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
