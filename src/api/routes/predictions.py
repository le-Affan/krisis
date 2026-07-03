from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from src.adapters import ModelInvocationError
from src.api.main import get_framework
from src.api.schemas.requests import OutcomeReportRequest, PredictionRequest
from src.api.schemas.responses import PredictionResponse
from src.core import ABTestFramework

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Route prediction through experiment",
    description="Routes an incoming request to one of the experiment's model variants and logs the request for later outcome analysis.",
)
async def predict(
    request: PredictionRequest, framework: ABTestFramework = Depends(get_framework)
):
    """Route a prediction request through the experiment"""
    try:
        # Use the experiment's configured traffic split (falls back to 0.5 for
        # backends/experiments that don't have a persisted config).
        probability_split = framework.storage.get_probability_split(
            request.experiment_id
        )
        prediction, request_id, variant = framework.route_request(
            request.features,
            probability_split=probability_split,
            experiment_id=request.experiment_id,
        )

        return PredictionResponse(
            request_id=request_id,
            prediction=prediction,
            model_variant=variant,  # Return actual variant
            timestamp=datetime.utcnow().isoformat(),
        )
    except ModelInvocationError as e:
        # The registered model itself failed (unreachable http endpoint, bad
        # response, or a raised exception in a python_callable). This is a
        # per-request failure, not a service crash.
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        # Experiment or model_id not found.
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/outcomes",
    summary="Report outcome",
    description="Submit the real-world outcome of a previously logged prediction using its request_id.",
)
async def report_outcome(
    request: OutcomeReportRequest, framework: ABTestFramework = Depends(get_framework)
):
    """Report a delayed outcome for a previous prediction"""
    try:
        framework.record_delayed_outcome(str(request.request_id), request.value)
        return {"status": "success", "request_id": str(request.request_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
