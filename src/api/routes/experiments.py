from fastapi import APIRouter, Depends, HTTPException

from src.api.main import get_framework
from src.api.schemas.requests import ExperimentCreateRequest, ExperimentUpdateRequest
from src.api.schemas.responses import ExperimentResponse
from src.core import ABTestFramework

router = APIRouter()


@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    request: ExperimentCreateRequest, framework: ABTestFramework = Depends(get_framework)
):
    try:
        for m_id in (request.model_a_id, request.model_b_id):
            if framework.storage.get_model(m_id) is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Model '{m_id}' is not registered. Register it via "
                        "POST /api/v1/models first."
                    ),
                )

        try:
            exp = framework.storage.create_experiment(
                experiment_id=request.experiment_id,
                model_a_id=request.model_a_id,
                model_b_id=request.model_b_id,
                probability_split=request.probability_split,
                metric_type=request.metric_type,
                confidence_level=request.confidence_level,
            )
        except ValueError:
            raise HTTPException(status_code=409, detail="Experiment already exists")

        return ExperimentResponse(**exp)

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str, framework: ABTestFramework = Depends(get_framework)):
    try:
        exp = framework.storage.get_experiment(experiment_id)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found.")
        return ExperimentResponse(**exp)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    request: ExperimentUpdateRequest,
    framework: ABTestFramework = Depends(get_framework),
):
    try:
        allowed_statuses = {"running", "paused", "completed"}
        if request.status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid status value.")

        exp = framework.storage.update_experiment_status(experiment_id, request.status)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found.")

        return ExperimentResponse(**exp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments", response_model=list[ExperimentResponse])
async def list_all_experiments(framework: ABTestFramework = Depends(get_framework)):
    try:
        return [ExperimentResponse(**exp) for exp in framework.storage.list_experiments()]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
