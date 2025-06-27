from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

import math

@dataclass
class InventoryChange:
    """Entidad que representa un cambio de inventario detectado"""
    sku: str
    id_location: int
    shopify_location_gid: str
    old_quantity: float
    new_quantity: float
    shopify_inventory_item: str
    sync_op: str
    title: str
    price: float
    price_compare: float
    priority: int = 3  # 1=crítico, 2=alto, 3=normal
    estimated_cost: Decimal = Decimal('0.01')
    
    
    def get_quantity_delta(self) -> int:
        """Regla de negocio: Calcular diferencia"""
        return math.ceil(self.new_quantity) - math.ceil(self.old_quantity)
    
    def should_update(self) -> bool:
        """Regla de negocio: ¿Vale la pena gastar en este update?"""
        print(self.sync_op)
        return (abs(self.get_quantity_delta()) > 0 or self.priority <= 3) and self.sync_op == "UPDATE"

    def is_new_product(self) -> bool:
        """Regla para saber si un producto debe ser creado en shopify"""
        print(self.sync_op)
        return self.sync_op == "CREATE"
    