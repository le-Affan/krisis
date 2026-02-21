from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ModelRegistrationRequest(BaseModel):
    model_id: str = Field(..., description="Unique model identifier")
    adapter_type: str = Field(..., description="python_callable or http_endpoint")
    location: str = Field(..., description="Import path or URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
