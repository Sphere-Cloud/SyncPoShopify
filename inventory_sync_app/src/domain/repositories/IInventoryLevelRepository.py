from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.ShopiProduct import ShopiProduct

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IInventoryLevelRepository(ABC):
    """Contrato para manejar inventario en PostgreSQL"""
    @abstractmethod
    async def get_current_inventory_levels(self) -> List[CacheInventoryLevel]:
        pass
    
    @abstractmethod
    async def products_created_on_shopify(self, shopi_products: List[ShopiProduct]) -> None:
        pass

    @abstractmethod
    async def update_inventory_level(self, inventory: CacheInventoryLevel) -> None:
        pass