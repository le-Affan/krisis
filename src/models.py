from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

@dataclass
class ModelVariant(Enum):
    A = "A"
    B = "B"

@dataclass
class Model:
    model_id: str
    callable: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Request:
    request_id: str
    selected_model: ModelVariant
    input_data: Any
    timestamp: float

@dataclass
class Outcome:
    request_id: str
    outcome_value: float
    timestamp: float

@dataclass
class ExperimentConfig:
    experiment_id: str
    model_a_id: str
    model_b_id: str
    traffic_split: float  # Probability of routing to model A
    confidence_level: float
    metric_type: str # "binary" or "continuous"
    status: str