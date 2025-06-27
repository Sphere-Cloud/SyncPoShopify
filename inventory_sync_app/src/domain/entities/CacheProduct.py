from ERPProduct import ERPProduct

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

@dataclass
class CacheProduct:
    """Entidad que representa un producto en Shopify (tabla shopify_product)"""
    pos_sku: str
    title: str
    description: str
    category: str
    sync_op: str
    shopify_product_gid: str
    shopify_variant_gid: str
    shopify_inventory_item_gid: str
    created_at: datetime
    updated_at: datetime
    
    def is_active(self) -> bool:
        """Regla de negocio: ¿Está activo en Shopify?"""
        return self.status == "active"
    
    def needs_update_from_erp(self, erp_product: ERPProduct) -> bool:
        """Regla de negocio: ¿Necesita actualización desde ERP?"""
        return (
            self.title != erp_product.descripcion or
            self.category != erp_product.get_category()
        )