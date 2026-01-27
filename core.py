# venv\Scripts\activate

import random
import uuid
import time
import numpy as np
from scipy import stats
import math


# In-Memory state
models = {}
requests = {}
outcomes = {}


# model registration function
def register_models(model_a, model_b):
    models["A"] = model_a
    models["B"] = model_b


# request routing function
def route_request(X, probability_split):

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
    requests[request_id] = {
        "input": X,
        "model": selected_model,
        "timestamp": timestamp
    }

    # Get prediction from the selected model
    prediction = models[selected_model](X)

    return prediction, request_id


# function to record the delayed outcome
def record_delayed_outcome(request_id, outcome):
    if request_id not in requests:
        raise ValueError("Request ID not found")

    outcomes[request_id] = outcome



# function to compute statistics
def compute_statistics():
    outcomes_A = []
    outcomes_B = []

    for request_id, outcome in outcomes.items():
        model_used = requests[request_id]["model"]
        if model_used == "A":
            outcomes_A.append(outcome)
        elif model_used == "B":
            outcomes_B.append(outcome)

    if len(outcomes_A) < 2 or len(outcomes_B) < 2: # ensures enough data for variance calculation
        return None

    mean_A = np.mean(outcomes_A)
    mean_B = np.mean(outcomes_B)

    var_A = np.var(outcomes_A, ddof=1)
    var_B = np.var(outcomes_B, ddof=1)

    n_A = len(outcomes_A)
    n_B = len(outcomes_B)

    # Standard error (Welch)
    se = math.sqrt(var_A / n_A + var_B / n_B)

    # Degrees of freedom (Welch–Satterthwaite)
    df = (var_A / n_A + var_B / n_B) ** 2 / (
        (var_A**2) / (n_A**2 * (n_A - 1)) +
        (var_B**2) / (n_B**2 * (n_B - 1))
    )

    # 95% CI
    t_crit = stats.t.ppf(0.975, df)
    delta = mean_B - mean_A

    lower = delta - t_crit * se
    upper = delta + t_crit * se

    return [mean_A, mean_B, delta, (lower, upper), n_A, n_B]


# function to compile all evidence
def compile_evidence():
    stats_result = compute_statistics()
    if stats_result is None:
        return "Not enough data to compute statistics."

    mean_A, mean_B, delta, (lower, upper), n_A, n_B = stats_result

    evidence = {
        "Model A Mean Outcome": round(mean_A, 4),
        "Model B Mean Outcome": round(mean_B, 4),
        "Difference in Means (B - A)": round(delta, 4),
        "95% Confidence Interval": (round(lower, 4), round(upper, 4)),
        "Number of Outcomes for Model A": n_A,
        "Number of Outcomes for Model B": n_B
    }

    return evidence