from abc import ABC, abstractmethod

class IChangeDetector(ABC):
    """Contrato para detectar cambios"""
    @abstractmethod
    async def detect_inventory_changes(
        self, 
        erp_products: List[ERPProduct],
        current_inventory: List[ShopifyInventoryLevel]
    ) -> List[InventoryChange]:
        pass