import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from src.db_models import DBRequest
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
    def get_outcomes_by_variant(self, variant: ModelVariant) -> List[float]:
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

    def get_outcomes_by_variant(self, variant: ModelVariant) -> List[float]:
        res = []
        for request_id, outcome in self.outcomes.items():
            try:
                if self.requests[request_id].selected_model == variant:
                    res.append(outcome.outcome_value)
            except KeyError:
                continue
        return res


class DatabaseStorage(StorageBackend):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_request(self, request: Request) -> None:
        session = self.session_factory()

        try:
            db_request = DBRequest(
                request_id=request.request_id,
                experiment_id="default",  # Will add later
                model_variant=request.model_variant.value,
                timestamp=datetime.fromtimestamp(request.timestamp),
                metadata=request.request_metadata,
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
                value=outcome.value,
                timestamp=datetime.fromtimestamp(outcome.timestamp),
            )
            session.add(db_outcome)
            session.commit()
        finally:
            session.close()

    def get_outcomes_by_variant(self, variant: ModelVariant) -> List[float]:
        session = self.session_factory()
        try:
            # Join requests and outcomes to filter by variant
            results = (
                session.query(DBOutcome.value)
                .join(DBRequest, DBRequest.request_id == DBOutcome.request_id)
                .filter(DBRequest.model_variant == variant.value)
                .all()
            )
            return [r[0] for r in results]
        finally:
            session.close()
