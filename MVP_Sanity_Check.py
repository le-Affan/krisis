def dummyA(X_A):
    return X_A + 1

def dummyB(X_B):
    return X_B * 2

from src.core import (
    register_models,
    route_request,
    record_delayed_outcome,
    requests,
    compile_evidence
)   


register_models(dummyA, dummyB)
request_IDs = []

for _ in range(100):
    pred, req_id = route_request(1, 0.5)
    request_IDs.append(req_id)

for ID in request_IDs:
    model_used = requests[ID]["model"]

    import random
    if model_used == "A":
        outcome = 0.5 + random.normalvariate(0, 0.01)
    else:
        outcome = 0.7 + random.normalvariate(0, 0.01)

    record_delayed_outcome(ID, outcome)

print(compile_evidence())

'''
Output:
{
'Model A Mean Outcome': np.float64(0.5003), 
'Model B Mean Outcome': np.float64(0.6991), 
'Difference in Means (B - A)': np.float64(0.1988), 
'95% Confidence Interval': (np.float64(0.1947), np.float64(0.2029)), 
'Number of Outcomes for Model A': 57, 
'Number of Outcomes for Model B': 43
}
'''
