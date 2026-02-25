from typing import Any, Dict, Optional

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


class OutcomeReportRequest(BaseModel):
    request_id: str
    value: float
    timestamp: Optional[str] = None  # ISO format, auto if not provided


class ExperimentUpdateRequest(BaseModel):
    status: str  # "running", "paused", "completed"
