from domain.entities.InventoryChange import InventoryChange
from domain.entities.ProductSyncLog import ProductSyncLog

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IShopifyUpdater(ABC):
    """Contrato para actualizar Shopify"""
    @abstractmethod
    async def update_inventory_batch(self, changes: List[InventoryChange]) -> List[ProductSyncLog]:
        pass