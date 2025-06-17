from abc import ABC, abstractmethod

class IProductRepository(ABC):
    """Contrato para manejar productos en PostgreSQL"""
    @abstractmethod
    async def get_all_shopify_products(self) -> List[ShopifyProduct]:
        pass
    
    @abstractmethod
    async def upsert_shopify_product(self, product: ShopifyProduct) -> None:
        pass