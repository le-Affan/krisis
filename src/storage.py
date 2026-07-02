from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import func

from src.db_models import DBExperiments, DBOutcome, DBRequest
from src.models import ModelVariant, Outcome, Request


class StorageBackend(ABC):
    # Abstract interface for data storage

    @abstractmethod
    def save_request(self, request: Request) -> None:
        pass

    @abstractmethod
    def save_outcome(self, outcome: Outcome) -> None:
        pass

    @abstractmethod
    def get_request(self, request_id: str) -> Optional[Request]:
        pass

    @abstractmethod
    def get_all_outcomes(self) -> Dict[str, Outcome]:
        pass

    @abstractmethod
    def get_outcomes_by_variant(self, variant: ModelVariant, experiment_id: str = None) -> List[float]:
        pass

    @abstractmethod
    def get_probability_split(self, experiment_id: str, default: float = 0.5) -> float:
        pass

    @abstractmethod
    def get_experiment_count(self) -> int:
        pass

    @abstractmethod
    def get_request_count(self) -> int:
        pass

    @abstractmethod
    def get_outcome_count(self) -> int:
        pass


class InMemoryStorage(StorageBackend):
    def __init__(self):
        self.requests: Dict[str, Request] = {}
        self.outcomes: Dict[str, Outcome] = {}

    def save_request(self, request) -> None:
        self.requests[request.request_id] = request

    def save_outcome(self, outcome) -> None:
        self.outcomes[outcome.request_id] = outcome

    def get_request(self, request_id) -> Optional[Request]:
        if request_id in self.requests:
            return self.requests[request_id]
        return None

    def get_all_outcomes(self) -> Dict[str, Outcome]:
        return self.outcomes

    def get_outcomes_by_variant(self, variant: ModelVariant, experiment_id: str = None) -> List[float]:
        res = []
        for request_id, outcome in self.outcomes.items():
            try:
                req = self.requests[request_id]
                if req.selected_model == variant and (experiment_id is None or req.experiment_id == experiment_id):
                    res.append(outcome.outcome_value)
            except KeyError:
                continue
        return res

    def get_probability_split(self, experiment_id: str, default: float = 0.5) -> float:
        # In-memory storage does not persist experiment configs; use the default.
        return default

    def get_experiment_count(self) -> int:
        # In-memory storage does not track experiments
        return 0

    def get_request_count(self) -> int:
        return len(self.requests)

    def get_outcome_count(self) -> int:
        return len(self.outcomes)


class DatabaseStorage(StorageBackend):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def _get_or_create_experiment(self, session, experiment_id: str):
        exp = session.query(DBExperiments).filter(DBExperiments.experiment_id == experiment_id).first()
        if not exp:
            exp = DBExperiments(experiment_id=experiment_id)
            session.add(exp)
            session.flush()

    def save_request(self, request: Request) -> None:
        session = self.session_factory()

        try:
            self._get_or_create_experiment(session, request.experiment_id)

            db_request = DBRequest(
                request_id=request.request_id,
                experiment_id=request.experiment_id,
                model_variant=request.selected_model.value,
                timestamp=datetime.fromtimestamp(request.timestamp),
            )

            session.add(db_request)
            session.commit()
        finally:
            session.close()

    def save_outcome(self, outcome: Outcome) -> None:
        session = self.session_factory()
        try:
            db_outcome = DBOutcome(
                request_id=outcome.request_id,
                value=outcome.outcome_value,
                timestamp=datetime.fromtimestamp(outcome.timestamp),
            )
            session.add(db_outcome)
            session.commit()
        finally:
            session.close()

    def get_request(self, request_id: str) -> Optional[Request]:
        session = self.session_factory()
        try:
            db_request = (
                session.query(DBRequest)
                .filter(DBRequest.request_id == request_id)
                .first()
            )

            if db_request is None:
                return None

            return Request(
                request_id=db_request.request_id,
                selected_model=ModelVariant(db_request.model_variant),
                input_data=None,  # Not persisted in DB
                timestamp=db_request.timestamp.timestamp(),
                experiment_id=db_request.experiment_id,
            )
        finally:
            session.close()

    def get_all_outcomes(self) -> Dict[str, Outcome]:
        session = self.session_factory()
        try:
            db_outcomes = session.query(DBOutcome).all()

            outcomes = {}
            for db_outcome in db_outcomes:
                outcomes[db_outcome.request_id] = Outcome(
                    request_id=db_outcome.request_id,
                    outcome_value=db_outcome.value,
                    timestamp=db_outcome.timestamp.timestamp(),
                )

            return outcomes
        finally:
            session.close()

    def get_outcomes_by_variant(self, variant: ModelVariant, experiment_id: str = None) -> List[float]:
        session = self.session_factory()
        try:
            # Join requests and outcomes to filter by variant
            query = (
                session.query(DBOutcome.value)
                .join(DBRequest, DBRequest.request_id == DBOutcome.request_id)
                .filter(DBRequest.model_variant == variant.value)
            )
            if experiment_id:
                query = query.filter(DBRequest.experiment_id == experiment_id)
            results = query.all()
            return [r[0] for r in results]
        finally:
            session.close()

    def get_probability_split(self, experiment_id: str, default: float = 0.5) -> float:
        session = self.session_factory()
        try:
            split = (
                session.query(DBExperiments.probability_split)
                .filter(DBExperiments.experiment_id == experiment_id)
                .scalar()
            )
            return split if split is not None else default
        finally:
            session.close()

    def get_experiment_count(self) -> int:
        session = self.session_factory()
        try:
            count = session.query(func.count(DBExperiments.experiment_id)).scalar()
            return count or 0
        finally:
            session.close()

    def get_request_count(self) -> int:
        session = self.session_factory()
        try:
            count = session.query(func.count(DBRequest.request_id)).scalar()
            return count or 0
        finally:
            session.close()

    def get_outcome_count(self) -> int:
        session = self.session_factory()
        try:
            count = session.query(func.count(DBOutcome.request_id)).scalar()
            return count or 0
        finally:
            session.close()
