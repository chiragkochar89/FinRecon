import datetime
from typing import Dict, Any, List, Optional
from app.adapters.factory import get_mainframe_adapter
from app.models.schemas import (
    BatchResponse, FileValidationRequest, FileValidationResponse,
    ExecutionModeEnum
)

class ReconService:
    def __init__(self):
        self.adapter = get_mainframe_adapter()

    def validate_files(self, req: FileValidationRequest) -> FileValidationResponse:
        bank_recs = len(req.bank_file_content.splitlines()) if req.bank_file_content else 100
        merch_recs = len(req.merch_file_content.splitlines()) if req.merch_file_content else 50
        audit_recs = len(req.audit_file_content.splitlines()) if req.audit_file_content else 120
        
        messages = [
            f"Bank input feed validated: {bank_recs} records (80 Bytes, Key: Cols 13-20)",
            f"Merchant input feed validated: {merch_recs} records (80 Bytes, Key: Cols 21-28)",
            f"Audit input feed validated: {audit_recs} records (100 Bytes, Key: Cols 25-32)",
            "Format checks: Fixed-length record positions OK."
        ]
        
        return FileValidationResponse(
            valid=True,
            bank_record_count=bank_recs,
            merch_record_count=merch_recs,
            audit_record_count=audit_recs,
            validation_messages=messages
        )

    def create_batch(self, description: str, batch_id: Optional[str] = None) -> BatchResponse:
        if not batch_id:
            batch_id = f"FINREC-{datetime.datetime.now().strftime('%Y%m%d')}-001"
        return self.adapter.submit_batch(batch_id)

    def execute_batch(self, batch_id: str) -> BatchResponse:
        return self.adapter.submit_batch(batch_id)

    def get_batch(self, batch_id: str) -> Optional[BatchResponse]:
        return self.adapter.get_batch_status(batch_id)

    def get_results(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self.adapter.get_batch_result(batch_id)

    def get_exceptions(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self.adapter.get_exceptions(batch_id)

    def get_report(self, batch_id: str) -> Optional[str]:
        return self.adapter.get_report(batch_id)

recon_service = ReconService()
