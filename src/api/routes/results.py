from fastapi import APIRouter, Depends, HTTPException

from src.api.main import get_framework
from src.api.schemas.responses import StatisticalResults
from src.core import ABTestFramework

router = APIRouter()


@router.get("/experiments/{experiment_id}/results", response_model=StatisticalResults)
async def get_results(
    experiment_id: str, framework: ABTestFramework = Depends(get_framework)
):
    """Get current statistical results for an experiment"""
    try:
        evidence = framework.compile_evidence()
        if evidence == "Not enough data to compute statistics.":
            raise HTTPException(status_code=400, detail=evidence)
        return StatisticalResults(
            experiment_id=experiment_id,
            model_a_mean=evidence["Model A Mean Outcome"],
            model_b_mean=evidence["Model B Mean Outcome"],
            difference=evidence["Difference in Means (B - A)"],
            confidence_interval=evidence["95% Confidence Interval"],
            sample_size_a=evidence["Number of Outcomes for Model A"],
            sample_size_b=evidence["Number of Outcomes for Model B"],
            confidence_level=0.95,
            warnings=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
