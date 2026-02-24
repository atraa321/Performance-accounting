from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import DATABASE_URL, SQL_ECHO

Base = declarative_base()


def get_engine(url: Optional[str] = None):
    return create_engine(url or DATABASE_URL, echo=SQL_ECHO, future=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
