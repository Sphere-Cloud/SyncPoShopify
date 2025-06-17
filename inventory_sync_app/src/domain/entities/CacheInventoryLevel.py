from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

@dataclass
class ShopifyInventoryLevel:
    """Entidad que representa inventario en Shopify (tabla shopify_inventory_level)"""
    inventory_level_id: int
    pos_sku: str
    shopify_inventory_level_gid: str
    location_name: str
    quantities_available: int
    updated_at: datetime
    
    def needs_inventory_update(self, new_quantity: int, threshold: int = 5) -> bool:
        """Regla de negocio: ¿Vale la pena actualizar? (optimización de costos)"""
        return abs(self.quantities_available - new_quantity) >= threshold
    
    def is_critical_change(self, new_quantity: int) -> bool:
        """Regla de negocio: ¿Es un cambio crítico? (stock out/in)"""
        return (self.quantities_available > 0 and new_quantity == 0) or \
               (self.quantities_available == 0 and new_quantity > 0)