import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.main import get_framework
from src.api.schemas.requests import SampleSizeRequest
from src.api.schemas.responses import (
    SampleSizeResponse,
    StatisticalResults,
    TimeseriesBucket,
    TimeseriesResponse,
)
from src.config import get_settings
from src.core import ABTestFramework
from src.models import ModelVariant
from src.statistics import (
    compute_guardrail_warnings,
    compute_statistics,
    required_sample_size_two_proportions,
)

router = APIRouter()


@router.get("/experiments/{experiment_id}/results", response_model=StatisticalResults)
async def get_results(
    experiment_id: str, framework: ABTestFramework = Depends(get_framework)
):
    """Get current statistical results for an experiment, including guardrail
    warnings (sample size, assignment imbalance, high variance)."""
    try:
        evidence = framework.compile_evidence(experiment_id=experiment_id)
        if evidence == "Not enough data to compute statistics.":
            raise HTTPException(status_code=400, detail=evidence)

        settings = get_settings()
        outcomes_a = framework.storage.get_outcomes_by_variant(
            ModelVariant.A, experiment_id
        )
        outcomes_b = framework.storage.get_outcomes_by_variant(
            ModelVariant.B, experiment_id
        )
        count_a = framework.storage.get_request_count_by_variant(
            ModelVariant.A, experiment_id
        )
        count_b = framework.storage.get_request_count_by_variant(
            ModelVariant.B, experiment_id
        )
        configured_split = framework.storage.get_probability_split(experiment_id)

        warnings = compute_guardrail_warnings(
            outcomes_a,
            outcomes_b,
            configured_split=configured_split,
            count_A=count_a,
            count_B=count_b,
            min_sample=settings.min_recommended_sample_size,
        )

        return StatisticalResults(
            experiment_id=experiment_id,
            model_a_mean=evidence["Model A Mean Outcome"],
            model_b_mean=evidence["Model B Mean Outcome"],
            difference=evidence["Difference in Means (B - A)"],
            confidence_interval=evidence["95% Confidence Interval"],
            sample_size_a=evidence["Number of Outcomes for Model A"],
            sample_size_b=evidence["Number of Outcomes for Model B"],
            confidence_level=0.95,
            warnings=warnings,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sample-size-calculator", response_model=SampleSizeResponse)
async def sample_size_calculator(request: SampleSizeRequest):
    """Required sample size per variant to detect a given effect between two
    proportions, via standard normal-approximation power analysis."""
    if request.baseline_rate + request.minimum_detectable_effect >= 1:
        raise HTTPException(
            status_code=400,
            detail="baseline_rate + minimum_detectable_effect must be < 1",
        )

    n = required_sample_size_two_proportions(
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
        power=request.power,
        alpha=request.alpha,
    )

    return SampleSizeResponse(
        required_sample_size_per_variant=n,
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
        power=request.power,
        alpha=request.alpha,
    )


_WINDOW_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
# Fixed-count fallback bounds so tight time ranges still yield a plottable curve.
_MIN_BUCKETS = 3
_MAX_BUCKETS = 50
_FALLBACK_BUCKETS = 10


def _parse_window_seconds(window: str) -> float:
    match = re.fullmatch(r"(\d+)([smhd])", window.strip().lower())
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid window; use forms like '30s', '10m', '1h', '1d'",
        )
    value, unit = int(match.group(1)), match.group(2)
    if value <= 0:
        raise HTTPException(status_code=400, detail="window must be positive")
    return value * _WINDOW_UNITS[unit]


@router.get(
    "/experiments/{experiment_id}/timeseries", response_model=TimeseriesResponse
)
async def get_timeseries(
    experiment_id: str,
    window: str = Query("1h", description="Bucket width, e.g. 30s, 10m, 1h, 1d"),
    framework: ABTestFramework = Depends(get_framework),
):
    """Cumulative statistics over time, so a caller can plot how the effect-size
    confidence interval narrows as data accumulates. Uses duration buckets, but
    falls back to fixed-count buckets when the time range is too tight/large."""
    window_seconds = _parse_window_seconds(window)

    events = framework.storage.get_outcome_events(experiment_id)
    if not events:
        return TimeseriesResponse(experiment_id=experiment_id, window=window, buckets=[])

    t0 = events[0]["timestamp"]
    t1 = events[-1]["timestamp"]
    span = t1 - t0

    if span <= 0:
        n_buckets = 1
    else:
        n_buckets = max(1, -(-int(span) // int(window_seconds)))  # ceil div
        if n_buckets < _MIN_BUCKETS or n_buckets > _MAX_BUCKETS:
            n_buckets = _FALLBACK_BUCKETS

    buckets = []
    for i in range(1, n_buckets + 1):
        edge = t1 if i == n_buckets else t0 + span * i / n_buckets
        vals_a = [e["value"] for e in events if e["timestamp"] <= edge and e["variant"] == "A"]
        vals_b = [e["value"] for e in events if e["timestamp"] <= edge and e["variant"] == "B"]

        bucket = TimeseriesBucket(
            timestamp=datetime.fromtimestamp(edge, tz=timezone.utc).isoformat(),
            sample_size_a=len(vals_a),
            sample_size_b=len(vals_b),
            mean_a=round(sum(vals_a) / len(vals_a), 4) if vals_a else None,
            mean_b=round(sum(vals_b) / len(vals_b), 4) if vals_b else None,
        )

        stats_result = compute_statistics(vals_a, vals_b)
        if stats_result is not None:
            bucket.effect_size = round(stats_result["effect_size"], 4)
            bucket.ci_lower = round(stats_result["ci_lower"], 4)
            bucket.ci_upper = round(stats_result["ci_upper"], 4)

        buckets.append(bucket)

    return TimeseriesResponse(
        experiment_id=experiment_id, window=window, buckets=buckets
    )
