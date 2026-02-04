from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from src.models import Request, Outcome, ModelVariant

class StorageBackend(ABC):
    # Abstract interface for data storage

    @abstractmethod
    def save_request(self, request : Request) -> None:
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
    
    def save_outcome(self, outcome)-> None:
        self.outcomes[outcome.request_id] = outcome
    
    def get_request(self, request_id)-> Optional[Request]:
        if request_id in self.requests:
            return self.requests[request_id]
        return None

    def get_all_outcomes(self) -> Dict[str, Outcome]:
         return self.outcomes
    

