from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from src.database import Base

# this is like just writing SQL queries


class DBModel(Base):
    __tablename__ = "models"

    model_id = Column(String(255), primary_key=True)
    adapter_type = Column(String(50))  #'python callable', 'http_endpoint'
    location = Column(String(50))  # path or URL
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
