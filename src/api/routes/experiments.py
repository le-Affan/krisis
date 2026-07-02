from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException

from src.api.main import get_framework
from src.api.schemas.requests import ExperimentCreateRequest, ExperimentUpdateRequest
from src.api.schemas.responses import ExperimentResponse
from src.config import get_settings
from src.core import ABTestFramework
from src.database import get_engine, get_session_factory
from src.db_models import DBExperiments

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

        settings = get_settings()
        engine = get_engine(settings.database_url)
        session_factory = get_session_factory(engine)
        session = session_factory()

        try:
            existing = session.get(DBExperiments, request.experiment_id)
            if existing:
                raise HTTPException(status_code=409, detail="Experiment already exists")

            db_experiment = DBExperiments(
                experiment_id=request.experiment_id,
                model_a_id=request.model_a_id,
                model_b_id=request.model_b_id,
                probability_split=request.probability_split,
                metric_type=request.metric_type,
                confidence_level=request.confidence_level,
                status="running",
                created_at=datetime.utcnow(),
            )

            session.add(db_experiment)
            session.commit()

            return ExperimentResponse(
                experiment_id=cast(str, db_experiment.experiment_id),
                model_a_id=cast(str, db_experiment.model_a_id),
                model_b_id=cast(str, db_experiment.model_b_id),
                probability_split=cast(float, db_experiment.probability_split),
                metric_type=cast(str, db_experiment.metric_type),
                confidence_level=cast(float, db_experiment.confidence_level),
                status=cast(str, db_experiment.status),
            )

        finally:
            session.close()

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str):
    try:
        settings = get_settings()
        engine = get_engine(settings.database_url)
        session_factory = get_session_factory(engine)
        session = session_factory()

        try:
            db_experiment = session.get(DBExperiments, experiment_id)

            if not db_experiment:
                raise HTTPException(status_code=404, detail="Experiment not found.")

            return ExperimentResponse(
                experiment_id=cast(str, db_experiment.experiment_id),
                model_a_id=cast(str, db_experiment.model_a_id),
                model_b_id=cast(str, db_experiment.model_b_id),
                probability_split=cast(float, db_experiment.probability_split),
                metric_type=cast(str, db_experiment.metric_type),
                confidence_level=cast(float, db_experiment.confidence_level),
                status=cast(str, db_experiment.status),
            )

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(experiment_id: str, request: ExperimentUpdateRequest):
    try:
        settings = get_settings()
        engine = get_engine(settings.database_url)
        session_factory = get_session_factory(engine)
        session = session_factory()

        try:
            db_experiment = session.get(DBExperiments, experiment_id)

            if not db_experiment:
                raise HTTPException(status_code=404, detail="Experiment not found.")

            allowed_statuses = {"running", "paused", "completed"}

            if request.status not in allowed_statuses:
                raise HTTPException(status_code=400, detail="Invalid status value.")

            db_experiment.status = request.status  # type: ignore
            session.commit()

            return ExperimentResponse(  # type: ignore[attr-defined]
                experiment_id=cast(str, db_experiment.experiment_id),
                model_a_id=cast(str, db_experiment.model_a_id),
                model_b_id=cast(str, db_experiment.model_b_id),
                probability_split=cast(float, db_experiment.probability_split),
                metric_type=cast(str, db_experiment.metric_type),
                confidence_level=cast(float, db_experiment.confidence_level),
                status=cast(str, db_experiment.status),
            )

        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments", response_model=list[ExperimentResponse])
async def list_all_experiments():
    try:
        settings = get_settings()
        engine = get_engine(settings.database_url)
        session_factory = get_session_factory(engine)
        session = session_factory()

        try:
            experiments = session.query(DBExperiments).all()

            return [
                ExperimentResponse(
                    experiment_id=cast(str, exp.experiment_id),
                    model_a_id=cast(str, exp.model_a_id),
                    model_b_id=cast(str, exp.model_b_id),
                    probability_split=cast(float, exp.probability_split),
                    metric_type=cast(str, exp.metric_type),
                    confidence_level=cast(float, exp.confidence_level),
                    status=cast(str, exp.status),
                )
                for exp in experiments
            ]

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
