from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()

def get_engine(database_url: str, echo: bool = False):
    # Create database engine
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=echo
        )
    else:
        #PostgreSQL
        return create_engine(database_url,echo=echo,pool_pre_ping=True)
        
    