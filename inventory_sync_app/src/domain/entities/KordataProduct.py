from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class KordataProduct:
    """Entidad que representa un producto de Kordata"""

    # PROBLEMA 1: En dataclasses, None debe ser Optional[tipo]
    # PROBLEMA 2: Mejor usar valores por defecto que None para evitar errores
    id: Optional[int] = 0
    sku: str = ""
    modelo: str = ""
    talla: str = ""
    color: str = ""
    nombre: str = ""
    categoria: str = ""
    proveedor: str = ""
    marca: str = ""
    almacen: str = ""
    costo: float = 0.0
    precio_venta: float = 0.0
    existencia: float = 0.0
    reservado: float = 0.0
    disponible: float = 0.0

    def has_inventory(self) -> bool:
        """Regla de negocio: ¿Tiene inventario disponible?"""
        # PROBLEMA 3: Si existencia es None, esto falla
        # CORRECCIÓN: Validar None
        return (self.existencia or 0.0) > 0.0
    
    def get_category(self) -> str:
        """Regla de negocio: Obtener categoría limpia"""
        return self.categoria or "SIN_CATEGORIA"
    
    def is_valid_for_sync(self) -> bool:
        """Regla de negocio: ¿Se puede sincronizar?"""
        # PROBLEMA 4: Si sku es None, len(None) falla
        # PROBLEMA 5: Si precio_venta es None, comparación falla
        # CORRECCIÓN: Validar None
        return len(self.sku) > 0 and (self.precio_venta or 0.0) > 0