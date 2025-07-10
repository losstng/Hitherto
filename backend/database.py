from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")  # setting up the file

engine = create_engine(DATABASE_URL) #creating the engine to be use to connect tot he database

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #creating that single session for each request

Base = declarative_base() #the base is always to be declared later

def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")