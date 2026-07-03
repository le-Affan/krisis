"""Wraps the two trained spam classifiers (scripts/train_models.py) as
python_callable-compatible functions per the Krisis adapter contract
(src/adapters.py): each function takes the request's `features` dict and
returns a prediction value.

Contract for this demo: features = {"text": "<sms message>"}.
Prediction = 1 (spam) or 0 (ham), matching the trained models' label
encoding, so it can be compared directly against ground truth for outcome
scoring in the traffic simulation.

Register with Krisis via:
    POST /api/v1/models
    {"model_id": "spam_nb_baseline", "adapter_type": "python_callable",
     "location": "demo.spam_models:predict_model_a"}
    {"model_id": "spam_tfidf_logreg", "adapter_type": "python_callable",
     "location": "demo.spam_models:predict_model_b"}
"""

from pathlib import Path

import joblib

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

_bundle_a = joblib.load(MODELS_DIR / "model_a.joblib")
_bundle_b = joblib.load(MODELS_DIR / "model_b.joblib")


def predict_model_a(features):
    """Model A: keyword-count + Multinomial Naive Bayes."""
    text = features["text"]
    vec = _bundle_a["vectorizer"].transform([text])
    return int(_bundle_a["model"].predict(vec)[0])


def predict_model_b(features):
    """Model B: TF-IDF + Logistic Regression."""
    text = features["text"]
    vec = _bundle_b["vectorizer"].transform([text])
    return int(_bundle_b["model"].predict(vec)[0])
