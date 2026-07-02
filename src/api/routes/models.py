from fastapi import APIRouter, Depends, HTTPException

from src.adapters import VALID_ADAPTER_TYPES, ModelResolutionError, validate_adapter
from src.api.main import get_framework
from src.api.schemas.requests import ModelRegistrationRequest
from src.api.schemas.responses import ModelResponse
from src.core import ABTestFramework

router = APIRouter()


@router.post("/models", response_model=ModelResponse, status_code=201)
async def register_model(
    request: ModelRegistrationRequest, framework: ABTestFramework = Depends(get_framework)
):
    """Register a model so experiments can reference it by ID.

    adapter_type must be one of:
      - "http": location is a URL. Krisis POSTs the input features as JSON
        to it and expects back JSON containing a "prediction" field.
      - "python_callable": location is "module.path:function_name",
        importable in the SAME Python environment running Krisis.
        SECURITY: this executes local code — never use on a deployment
        reachable by untrusted users.

    For python_callable, the import is resolved immediately so a bad
    reference fails here (400) instead of at prediction time.
    """
    if request.adapter_type not in VALID_ADAPTER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid adapter_type '{request.adapter_type}'. Must be one "
                f"of: {sorted(VALID_ADAPTER_TYPES)}"
            ),
        )

    try:
        validate_adapter(request.adapter_type, request.location)
    except ModelResolutionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        framework.storage.save_model(
            request.model_id, request.adapter_type, request.location, request.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return ModelResponse(
        model_id=request.model_id,
        adapter_type=request.adapter_type,
        location=request.location,
        metadata=request.metadata or {},
    )


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, framework: ABTestFramework = Depends(get_framework)):
    model = framework.storage.get_model(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return ModelResponse(**model)


@router.get("/models", response_model=list[ModelResponse])
async def list_models(framework: ABTestFramework = Depends(get_framework)):
    return [ModelResponse(**m) for m in framework.storage.list_models()]
