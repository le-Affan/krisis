import random
import uuid
import time
import numpy as np


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

    if request_id in requests:
        outcomes[request_id] = outcome
    else:
        raise ValueError("Request ID not found")


# function to calculate per model statistics
def calculate_model_statistics():
    outcomes_A = []
    outcomes_B = []

    for request_id, outcome in outcomes.items():
        model_used = requests[request_id]["model"]
        if model_used == "A":
            outcomes_A.append(outcome)
        elif model_used == "B":
            outcomes_B.append(outcome)
    
    mean_A = np.mean(outcomes_A) if outcomes_A else None
    mean_B = np.mean(outcomes_B) if outcomes_B else None
    delta = (mean_B - mean_A) if (mean_A is not None and mean_B is not None) else None

    return {"A": mean_A, "B": mean_B, "delta": delta}