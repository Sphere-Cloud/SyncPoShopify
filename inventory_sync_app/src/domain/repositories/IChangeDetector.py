from domain.entities.ERPProduct import ERPProduct
from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.InventoryChange import InventoryChange

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IChangeDetector(ABC):
    """Contrato para detectar cambios"""
    @abstractmethod
    async def detect_inventory_changes(
        self, 
        erp_products: List[ERPProduct],
        current_inventory: List[CacheInventoryLevel]
    ) -> List[InventoryChange]:
        pass