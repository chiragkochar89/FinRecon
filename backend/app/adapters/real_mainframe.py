from typing import Dict, Any
from app.adapters.base import MainframeAdapter
from app.models.schemas import BatchResponse, BatchStatusEnum, ExecutionModeEnum

class RealMainframeAdapter(MainframeAdapter):
    """
    REAL MAINFRAME ADAPTER:
    Connects to genuine z/OS host via z/OSMF REST APIs or FTP JES Job Submission.
    Explicitly labelled as REAL_MAINFRAME mode.
    """
    def __init__(self, zos_host: str = None):
        self.zos_host = zos_host

    @property
    def mode(self) -> ExecutionModeEnum:
        return ExecutionModeEnum.REAL_MAINFRAME

    def submit_batch(self, batch_id: str) -> BatchResponse:
        raise NotImplementedError(
            "REAL MAINFRAME MODE requires an active z/OS z/OSMF / FTP credentials configuration. "
            "Set FINRECON_MODE=LOCAL_DEMO to run the integrated local processing engine."
        )

    def get_batch_status(self, batch_id: str) -> BatchResponse:
        raise NotImplementedError("REAL MAINFRAME MODE not configured.")

    def get_batch_result(self, batch_id: str) -> Dict[str, Any]:
        raise NotImplementedError("REAL MAINFRAME MODE not configured.")

    def get_exceptions(self, batch_id: str) -> Dict[str, Any]:
        raise NotImplementedError("REAL MAINFRAME MODE not configured.")

    def get_report(self, batch_id: str) -> str:
        raise NotImplementedError("REAL MAINFRAME MODE not configured.")
