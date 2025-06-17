from domain.repositories.IShopifyUpdater import IShopifyUpdater

from domain.entities.InventoryChange import InventoryChange
from domain.entities.ProductSyncLog import ProductSyncLog

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

class ShopifyInventoryUpdater(IShopifyUpdater):
    """IMPLEMENTACIÓN CONCRETA: Actualiza inventario en Shopify"""
    
    def __init__(self, shop_url: str, access_token: str):
        self._shop_url = shop_url
        self._access_token = access_token
        self._rate_limit_calls = 0
        self._rate_limit_max = 40  # Por segundo
    
    async def update_inventory_batch(self, changes: List[InventoryChange]) -> List[ProductSyncLog]:
        """Actualiza inventario respetando rate limits"""
        sync_results = []
        
        for change in changes:
            # Respetar rate limit
            if self._rate_limit_calls >= self._rate_limit_max:
                await asyncio.sleep(1)  # Esperar 1 segundo
                self._rate_limit_calls = 0
            
            try:
                # Simular llamada a Shopify API
                success = await self._update_single_inventory(change)
                
                sync_log = ProductSyncLog(
                    sync_id=0,  # Se asignará en la DB
                    sku_pos=change.sku,
                    sync_info=f"Updated from {change.old_quantity} to {change.new_quantity}",
                    before_sync=change.old_quantity,
                    after_sync=change.new_quantity,
                    synced_at=datetime.now(),
                    synced_status="SUCCESS" if success else "FAILED",
                    sync_type="INVENTORY"
                )
                sync_results.append(sync_log)
                
            except Exception as e:
                sync_log = ProductSyncLog(
                    sync_id=0,
                    sku_pos=change.sku,
                    sync_info=f"Error: {str(e)}",
                    before_sync=change.old_quantity,
                    after_sync=change.old_quantity,  # No cambió
                    synced_at=datetime.now(),
                    synced_status="FAILED",
                    sync_type="INVENTORY"
                )
                sync_results.append(sync_log)
        
        return sync_results
    
    async def _update_single_inventory(self, change: InventoryChange) -> bool:
        """Llamada real a Shopify API (simulada)"""
        self._rate_limit_calls += 1
        
        # Aquí iría tu llamada real a Shopify
        # Por ahora simulamos con un delay
        await asyncio.sleep(0.1)  # Simular latencia de red
        return True  # Simular éxito
