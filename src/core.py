# venv\Scripts\activate

import random
import time
import uuid
from typing import Optional

from src.adapters import invoke_model
from src.config import get_settings
from src.database import get_engine, get_session_factory
from src.models import Model, ModelVariant, Outcome, Request
from src.statistics import compute_statistics
from src.storage import DatabaseStorage, InMemoryStorage, StorageBackend


class ABTestFramework:
    def __init__(self, storage_backend: Optional[StorageBackend] = None):
        if storage_backend is None:
            settings = get_settings()
            if settings.storage_backend == "memory":
                self.storage = InMemoryStorage()
            else:
                engine = get_engine(settings.database_url)
                # NOTE: Do NOT call init_db / Base.metadata.create_all here.
                # Schema is exclusively managed by Alembic migrations.
                # Run: alembic upgrade head  (before starting the app)
                session_factory = get_session_factory(engine)
                self.storage = DatabaseStorage(session_factory)
        else:
            self.storage = storage_backend
        self.models = {}

    # model registration function
    def register_models(self, model_a, model_b):
        """
        Directly inject variant callables, bypassing the model registry.

        Intended for tests and simple scripted use. Production traffic
        should instead register real models via POST /api/v1/models and
        reference them by ID in the experiment config — route_request will
        resolve those through the registry (see _invoke_variant below).

        Parameters:
        model_a : callable
            Function or callable object representing variant A.
        model_b : callable
            Function or callable object representing variant B.

        Behavior:
        - Stores the models in in-memory state under keys "A" and "B".
        - Overwrites any previously registered models.
        """
        self.models["A"] = Model(model_id="A", callable=model_a)
        self.models["B"] = Model(model_id="B", callable=model_b)

    def _invoke_variant(self, variant: ModelVariant, X, experiment_id: str):
        """Resolve which callable serves this variant and invoke it.

        If register_models() was used, that direct injection takes priority.
        Otherwise resolve the experiment's registered model_id from storage
        and dispatch through the model registry's adapter (http or
        python_callable). Raises ValueError if the experiment or model isn't
        found; adapter invocation failures raise ModelInvocationError.
        """
        model_key = variant.value
        if model_key in self.models:
            return self.models[model_key].callable(X)

        model_ids = self.storage.get_experiment_models(experiment_id)
        if model_ids is None:
            raise ValueError(f"Experiment '{experiment_id}' not found.")
        model_a_id, model_b_id = model_ids
        model_id = model_a_id if variant == ModelVariant.A else model_b_id

        model_record = self.storage.get_model(model_id)
        if model_record is None:
            raise ValueError(f"Model '{model_id}' not found in registry.")

        return invoke_model(model_record["adapter_type"], model_record["location"], X)

    # request routing function
    def route_request(self, X, probability_split, experiment_id="default"):
        """
        Route an incoming request to one of the registered model variants.

        Parameters:
        X : any
            Input data passed to the selected model.
        probability_split : float
            Probability of routing the request to model A (between 0 and 1).

        Returns:
        tuple
            (prediction, request_id, variant) where prediction is the model output,
            request_id uniquely identifies the routed request, and variant is "A" or "B".

        Behavior:
        - Randomly assigns the request to model A or B based on probability_split.
        - Stores request metadata (input, assigned model, timestamp) in memory.
        - Does not guarantee deterministic assignment across calls.
        """
        # Generate a unique request ID and timestamp
        request_id = str(uuid.uuid4())
        timestamp = time.time()

        # Select model based on probability split
        if random.random() < probability_split:
            variant = ModelVariant.A
        else:
            variant = ModelVariant.B

        # create a store request object
        request_object = Request(
            request_id=request_id,
            selected_model=variant,
            input_data=X,
            timestamp=timestamp,
            experiment_id=experiment_id,
        )
        self.storage.save_request(request_object)

        # Get prediction
        prediction = self._invoke_variant(variant, X, experiment_id)

        return prediction, request_id, variant.value

    # function to record the delayed outcome
    def record_delayed_outcome(self, request_id, outcome):
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
        request_object = self.storage.get_request(request_id)

        if request_object is None:
            raise ValueError(f"Request ID {request_id} not found.")

        outcome_object = Outcome(
            request_id=request_id, outcome_value=outcome, timestamp=time.time()
        )

        self.storage.save_outcome(outcome_object)
        # outcomes[request_id] = outcome

    # function to compile all evidence
    def compile_evidence(self, experiment_id: str = None):
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
        outcomes_A = self.storage.get_outcomes_by_variant(ModelVariant.A, experiment_id)
        outcomes_B = self.storage.get_outcomes_by_variant(ModelVariant.B, experiment_id)

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
            "Effect Size": round(effect_size, 4),
        }
        return evidence
