from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.main import get_framework
from src.api.schemas.requests import OutcomeReportRequest, PredictionRequest
from src.api.schemas.responses import PredictionResponse
from src.core import ABTestFramework

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest, framework: ABTestFramework = Depends(get_framework)
):
    """Route a prediction request through the experiment"""
    try:
        # Extract features and call route_request
        prediction, request_id = framework.route_request(
            request.features,
            probability_split=0.5,  # Get from experiment config
        )

        return PredictionResponse(
            request_id=request_id,
            prediction=prediction,
            model_variant="A",  # Return actual variant
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outcomes")
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
