from typing import Any, Optional

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


class ExperimentResponse(BaseModel):
    experiment_id: str
    model_a_id: str
    model_b_id: str
    probability_split: float
    metric_type: str
    confidence_level: float
    status: str


class SampleSizeResponse(BaseModel):
    required_sample_size_per_variant: int
    baseline_rate: float
    minimum_detectable_effect: float
    power: float
    alpha: float


class TimeseriesBucket(BaseModel):
    timestamp: str
    sample_size_a: int
    sample_size_b: int
    mean_a: Optional[float] = None
    mean_b: Optional[float] = None
    effect_size: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None


class TimeseriesResponse(BaseModel):
    experiment_id: str
    window: str
    buckets: list[TimeseriesBucket]
