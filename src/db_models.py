from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, String
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


class DBExperiments(Base):
    __tablename__ = "experiments"

    experiment_id = Column(String(255), primary_key=True)
    model_a_id = Column(String(255), ForeignKey("models.model_id"))
    model_b_id = Column(String(255), ForeignKey("models.model_id"))
    probability_split = Column(Float)
    metric_type = Column(String(50))  # binary or continuos
    confidence_level = Column(Float, default=0.95)
    status = Column(String(50), default="running")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class DBRequest(Base):
    __tablename__ = "requests"
    request_id = Column(String(255), primary_key=True)
    experiment_id = Column(String(255), ForeignKey("experiments.experiment_id"))
    model_variant = Column(String(10))  # "A" or "B"
    timestamp = Column(DateTime)
    metadata = Column(JSON)

    __table_args__ = (Index("idx_experiment_timestamp", "experiment_id", "timestamp"),)


class DBOutcome(Base):
    __tablename__ = "outcomes"
    request_id = Column(
        String(255), ForeignKey("requests.request_id"), primary_key=True
    )
    value = Column(Float)
    timestamp = Column(DateTime)
    __table_args__ = (Index("idx_request_id", "request_id"),)
