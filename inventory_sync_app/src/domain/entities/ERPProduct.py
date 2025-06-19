from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

@dataclass
class ERPProduct:
    """Entidad que representa un producto del ERP"""
    codigo: str
    descripcion: str
    unidad: str
    precio: Decimal
    precio_con_imp: Decimal
    existencia: float
    grupo2: Optional[str] = None
    desc_grupo2: Optional[str] = None
    agrupacion2: Optional[str] = None
    desc_agrup2: Optional[str] = None
    imagen_bit: str = ""
    
    def has_inventory(self) -> bool:
        """Regla de negocio: ¿Tiene inventario disponible?"""
        return self.existencia > 0.0
    
    def get_category(self) -> str:
        """Regla de negocio: Obtener categoría limpia"""
        return self.desc_grupo2 or "SIN_CATEGORIA"
    
    def is_valid_for_sync(self) -> bool:
        """Regla de negocio: ¿Se puede sincronizar?"""
        return len(self.codigo) > 0 and self.precio > 0