from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

import math

@dataclass
class CacheInventoryLevel:
    """Entidad que representa inventario en Shopify (tabla shopify_inventory_level)"""
    inventory_level_id: int
    pos_sku: str
    id_location: int
    shopify_inventory_level_gid: str
    quantities_available: int
    updated_at: datetime
    sync_op: str
    shopify_location_gid: str
    shopify_inventory_item_gid: str
    title: str
    price: float
    price_compare: float

    
    def should_update(self, new_quantity: float, threshold: int = 0) -> bool:
        """Regla de negocio: ¿Vale la pena actualizar? (optimización de costos)"""
        print(f"Should update {abs(self.quantities_available - math.ceil(new_quantity))}")
        return (abs(self.quantities_available - math.ceil(new_quantity)) > threshold) and self.sync_op == "UPDATE"   

    def is_new_product(self) -> bool:
        """Regla de negocio: ¿Es un nuevo producto?"""
        return self.sync_op == "CREATE"
    
    def is_critical_change(self, new_quantity: int) -> bool:
        """Regla de negocio: ¿Es un cambio crítico? (stock out/in)"""
        return (self.quantities_available > 0 and new_quantity == 0) or \
               (self.quantities_available == 0 and new_quantity > 0) or \
               (self.sync_op == "CREATE")