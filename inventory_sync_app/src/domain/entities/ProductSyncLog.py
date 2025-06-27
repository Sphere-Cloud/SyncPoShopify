from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

@dataclass
class ProductSyncLog:
    """Entidad que representa el log de sincronización (tabla product_sync_log)"""
    sync_id: int
    sku_pos: str
    sync_info: str
    before_sync: float
    after_sync: float
    synced_at: datetime
    synced_status: str
    sync_type: str
    
    def was_successful(self) -> bool:
        """Regla de negocio: ¿Fue exitoso?"""
        return self.synced_status == "SUCCESS"