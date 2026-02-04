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
