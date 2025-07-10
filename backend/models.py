from sqlalchemy import Column, Integer, Text, String, DateTime, JSON, Boolean, func
from .database import Base  # assumes you have a `Base = declarative_base()` in `database.py`



class Newsletter(Base):
    __tablename__ = "newsletter"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    sender = Column(String, nullable=False)
    received_at = Column(DateTime, nullable=False)
    extracted_text = Column(Text, nullable=True)
    chunked_text = Column(JSON, nullable=True)  # JSON array of text chunks
    message_id = Column(String, unique=True, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    vectorized = Column(Boolean, default=False)

