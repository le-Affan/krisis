# venv\Scripts\activate

import random
import uuid
import time
from src.statistics import compute_statistics

# In-Memory state
models = {}
requests = {}
outcomes = {}


# model registration function
def register_models(model_a, model_b):
    """
    Register two model variants for A/B testing.

    Parameters:
    model_a : callable
        Function or callable object representing variant A.
    model_b : callable
        Function or callable object representing variant B.

    Behavior:
    - Stores the models in in-memory state under keys "A" and "B".
    - Overwrites any previously registered models.
    """
    models["A"] = model_a
    models["B"] = model_b


# request routing function
def route_request(X, probability_split):
    """
    Route an incoming request to one of the registered model variants.

    Parameters:
    X : any
        Input data passed to the selected model.
    probability_split : float
        Probability of routing the request to model A (between 0 and 1).

    Returns:
    tuple
        (prediction, request_id) where prediction is the model output
        and request_id uniquely identifies the routed request.

    Behavior:
    - Randomly assigns the request to model A or B based on probability_split.
    - Stores request metadata (input, assigned model, timestamp) in memory.
    - Does not guarantee deterministic assignment across calls.
    """
    # Generate a unique request ID and timestamp
    request_id = str(uuid.uuid4())
    timestamp = time.time()

    # Select model based on probability split
    random_value = random.random()
    if random_value < probability_split:
        selected_model = "A"
    else:
        selected_model = "B"

    # Store the request details
    requests[request_id] = {"input": X, "model": selected_model, "timestamp": timestamp}

    # Get prediction from the selected model
    prediction = models[selected_model](X)

    return prediction, request_id


# function to record the delayed outcome
def record_delayed_outcome(request_id, outcome):
    """
    Record the observed outcome for a previously routed request.

    Parameters:
    request_id : str
        Unique identifier returned by route_request.
    outcome : float
        Observed outcome value associated with the request.

    Raises:
    ValueError
        If the request_id does not exist in the request log.

    Behavior:
    - Links the outcome to the original request via request_id.
    - Assumes a single outcome per request.
    """
    if request_id not in requests:
        raise ValueError("Request ID not found")

    outcomes[request_id] = outcome


# function to compile all evidence
def compile_evidence():
    """
    Aggregate recorded outcomes and produce a human-readable summary of
    statistical evidence for the A/B experiment.

    Returns:
    dict or str
        A dictionary containing rounded summary statistics, confidence interval,
        sample counts, and effect size if sufficient data is available.
        Returns a string message if there are fewer than the minimum required
        outcomes per variant.

    Behavior:
    - Groups recorded outcomes by model variant (A and B) using request metadata.
    - Delegates all statistical computation to compute_statistics.
    - Transforms raw statistical outputs into a presentation-friendly format
      (rounding values and applying descriptive labels).

    Notes:
    - This function performs no statistical calculations itself.
    - Intended as a presentation / reporting layer on top of compute_statistics.

    Assumptions:
    - Each request has at most one recorded outcome.
    - Requests and outcomes stores are consistent and in sync.
    - Outcomes are numeric and comparable across variants.
    """
    outcomes_A = []
    outcomes_B = []
    for req_id, outcome in outcomes.items():
        model_used = requests[req_id]["model"]
        if model_used == "A":
            outcomes_A.append(outcome)
        else:
            outcomes_B.append(outcome)
    stats_result = compute_statistics(outcomes_A, outcomes_B)
    if stats_result is None:
        return "Not enough data to compute statistics."

    mean_A = stats_result["mean_A"]
    mean_B = stats_result["mean_B"]
    delta = stats_result["delta"]
    ci_lower = stats_result["ci_lower"]
    ci_upper = stats_result["ci_upper"]
    n_A = stats_result["n_A"]
    n_B = stats_result["n_B"]
    effect_size = stats_result["effect_size"]


    evidence = {
        "Model A Mean Outcome": round(mean_A, 4),
        "Model B Mean Outcome": round(mean_B, 4),
        "Difference in Means (B - A)": round(delta, 4),
        "95% Confidence Interval": (round(ci_lower, 4), round(ci_upper, 4)),
        "Number of Outcomes for Model A": n_A,
        "Number of Outcomes for Model B": n_B,
        "Effect Size": round(effect_size, 4)
    }

    return evidence
