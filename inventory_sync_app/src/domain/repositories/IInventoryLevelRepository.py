from abc import ABC, abstractmethod

class IInventoryLevelRepository(ABC):
    """Contrato para manejar inventario en PostgreSQL"""
    @abstractmethod
    async def get_current_inventory_levels(self) -> List[ShopifyInventoryLevel]:
        pass
    
    @abstractmethod
    async def update_inventory_level(self, inventory: ShopifyInventoryLevel) -> None:
        pass