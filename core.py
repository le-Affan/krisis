import random
import uuid
import time


# In-Memory state
models = {}
requests = {}
outcomes = {}


# model registration function
def register_models(model_a, model_b):
    models["A"] = model_a
    models["B"] = model_b


#  request routing function
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


# delayed outcome recording function
def record_delayed_outcome(request_id, outcome):

    if request_id in requests:
        outcomes[request_id] = outcome
    else:
        raise ValueError("Request ID not found")