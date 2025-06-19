from domain.entities.CacheProduct import CacheProduct

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IProductRepository(ABC):
    """Contrato para manejar productos en PostgreSQL"""
    @abstractmethod
    async def get_all_shopify_products(self) -> List[CacheProduct]:
        pass
    
    @abstractmethod
    async def upsert_shopify_product(self, product: CacheProduct) -> None:
        pass