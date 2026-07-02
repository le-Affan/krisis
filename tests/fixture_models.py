"""Real local functions used by adapter/model-registry tests as
python_callable targets. Not a test file itself — a stand-in for a user's
own model code, imported by module path exactly like a real deployment
would import theirs."""


def add_one(features):
    return features["x"] + 1


def double(features):
    return features["x"] * 2


def broken_model(features):
    raise RuntimeError("simulated model failure")
