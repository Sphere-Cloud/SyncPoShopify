from domain.entities.InventoryChange import InventoryChange
from domain.entities.ProductSyncLog import ProductSyncLog
from domain.entities.ShopiProduct import ShopiProduct

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IShopifyUpdater(ABC):
    """Contrato para actualizar Shopify"""
    @abstractmethod
    async def update_inventory_batch(self, changes: List[InventoryChange]) -> List[ProductSyncLog]:
        pass
    
    @abstractmethod
    async def create_inventory_batch(self, changes: List[InventoryChange]) -> List[ShopiProduct]:
        pass

    @abstractmethod
    async def _update_single_inventory(self, change: InventoryChange) -> bool:
        pass

    @abstractmethod
    async def _create_single_inventory(self, change: InventoryChange) -> bool:
        pass