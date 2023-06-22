"""
A module to set up the database
"""
from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# All the things for setting up the database
SQLALCHEMY_DATABASE_URL = "sqlite:///wapp.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@event.listens_for(Engine, "connect")
def enable_cascade(dbapi_connection, _):
    """
    Cascade does not work without this and we need it for auto deleting icons and screenshots
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
