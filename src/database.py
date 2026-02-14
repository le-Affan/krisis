from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()
# this will tell SQLAlchemy "Any class that inherits from me is a database table."


def get_engine(database_url: str, echo: bool = False):
    # Create database engine
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=echo,
        )
    else:
        # PostgreSQL
        return create_engine(database_url, echo=echo, pool_pre_ping=True)


def get_session_factory(engine):
    # Create session factory
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine):
    # Initialize database schema
    Base.metadata.create_all(engine)
