from app.core.config import settings
from app.adapters.base import MainframeAdapter
from app.adapters.local_demo import LocalDemoAdapter
from app.adapters.real_mainframe import RealMainframeAdapter
from app.models.schemas import ExecutionModeEnum

def get_mainframe_adapter() -> MainframeAdapter:
    """Factory creating adapter instance based on FINRECON_MODE configuration."""
    if settings.FINRECON_MODE == ExecutionModeEnum.REAL_MAINFRAME.value:
        return RealMainframeAdapter()
    return LocalDemoAdapter(data_dir=settings.DATA_DIRECTORY)
