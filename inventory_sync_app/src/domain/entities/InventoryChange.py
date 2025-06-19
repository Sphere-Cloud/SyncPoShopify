from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

@dataclass
class InventoryChange:
    """Entidad que representa un cambio de inventario detectado"""
    sku: str
    location_name: str
    old_quantity: float
    new_quantity: float
    priority: int = 3  # 1=crítico, 2=alto, 3=normal
    estimated_cost: Decimal = Decimal('0.01')
    
    def get_quantity_delta(self) -> int:
        """Regla de negocio: Calcular diferencia"""
        return self.new_quantity - self.old_quantity
    
    def is_worth_updating(self) -> bool:
        """Regla de negocio: ¿Vale la pena gastar en este update?"""
        return abs(self.get_quantity_delta()) > 0 or self.priority <= 3