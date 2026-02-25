from datetime import datetime
from logging import exception
from typing import cast

from fastapi import APIRouter, HTTPException

from src.api.schemas.requests import ExperimentCreateRequest
from src.api.schemas.responses import ExperimentResponse
from src.config import get_settings
from src.database import get_engine, get_session_factory
from src.db_models import DBExperiments

router = APIRouter()


@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(request: ExperimentCreateRequest):
    try:
        settings = get_settings()
        engine = get_engine(settings.database_url)
        session_factory = get_session_factory(engine)
        session = session_factory()

        try:
            # Check if experiment already exists
            existing = session.get(DBExperiments, request.experiment_id)
            if existing:
                raise HTTPException(status_code=400, detail="Experiment already exists")

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
        raise HTTPException(status_code=500, detail=str(e))
