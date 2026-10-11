from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.schemas import BatchResponse, ExecutionModeEnum

class MainframeAdapter(ABC):
    @property
    @abstractmethod
    def mode(self) -> ExecutionModeEnum:
        """Return active execution mode."""
        pass

    @abstractmethod
    def submit_batch(self, batch_id: str) -> BatchResponse:
        """Submit/execute batch job."""
        pass

    @abstractmethod
    def get_batch_status(self, batch_id: str) -> Optional[BatchResponse]:
        """Get status of submitted batch."""
        pass

    @abstractmethod
    def get_batch_result(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed batch results."""
        pass

    @abstractmethod
    def get_exceptions(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get exception records for batch."""
        pass

    @abstractmethod
    def get_report(self, batch_id: str) -> Optional[str]:
        """Get formatted audit report."""
        pass
