from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# each of the following classes define the shape of a specific API request


class ModelRegistrationRequest(BaseModel):
    model_id: str = Field(..., description="Unique model identifier")
    adapter_type: str = Field(..., description="python_callable or http_endpoint")
    location: str = Field(..., description="Import path or URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExperimentCreateRequest(BaseModel):
    experiment_id: str
    model_a_id: str
    model_b_id: str
    probability_split: float = Field(
        0.5, ge=0, le=1, description="Probability of Model A"
    )
    # 0.5 → default value ; ge=0 → must be ≥ 0 ; le=1 → must be ≤ 1
    metric_type: str = Field("continuous", description="binary or continuous")
    confidence_level: float = Field(0.95, ge=0.5, le=0.999)


class PredictionRequest(BaseModel):
    experiment_id: str
    request_id: Optional[str] = None  # Auto-generate if not provided
    features: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "rec_model_test",
                "features": {"user_id": "123", "item_id": "456"},
                "metadata": {"user_segment": "premium"},
            }
        }


class OutcomeReportRequest(BaseModel):
    request_id: UUID
    value: float = Field(..., description="Outcome value", allow_inf_nan=False)
    timestamp: Optional[datetime] = None  # ISO format, auto if not provided

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "value": 1.0,
            }
        }


class ExperimentUpdateRequest(BaseModel):
    status: str  # "running", "paused", "completed"


class SampleSizeRequest(BaseModel):
    baseline_rate: float = Field(
        ..., gt=0, lt=1, description="Baseline conversion rate (0-1)"
    )
    minimum_detectable_effect: float = Field(
        ..., gt=0, lt=1, description="Absolute effect to detect (0-1)"
    )
    power: float = Field(0.8, gt=0, lt=1, description="Statistical power (0-1)")
    alpha: float = Field(0.05, gt=0, lt=1, description="Significance level (0-1)")
