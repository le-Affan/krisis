from typing import Any

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    request_id: str
    prediction: Any
    model_variant: str
    timestamp: str


class StatisticalResults(BaseModel):
    experiment_id: str
    model_a_mean: float
    model_b_mean: float
    difference: float
    confidence_interval: tuple[float, float]
    sample_size_a: int
    sample_size_b: int
    confidence_level: float
    warnings: list[str] = []


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    storage_backend: str
