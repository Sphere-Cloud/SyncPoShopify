from dataclasses import dataclass
from datetime import datatime

@dataclass
class CacheLocation:
    """Entidad que representa un producto en Shopify (tabla shopify product)"""
    id_location: int
    name: str
    shopify_location_gid: str