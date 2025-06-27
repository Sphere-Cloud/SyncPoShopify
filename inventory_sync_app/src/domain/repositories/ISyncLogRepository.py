from domain.entities.ProductSyncLog import ProductSyncLog
from abc import ABC, abstractmethod

class ISyncLogRepository(ABC):
    """Contrato para manejar logs de sincronización"""
    @abstractmethod
    async def create_sync_logs(self, sync_log: ProductSyncLog) -> int:
        pass