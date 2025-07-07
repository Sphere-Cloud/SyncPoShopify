from domain.repositories.IInventoryLevelRepository import IInventoryLevelRepository

from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.ShopiProduct import ShopiProduct
from domain.entities.InventoryChange import InventoryChange

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg

class PostgreSQLInventoryRepository(IInventoryLevelRepository):
    """IMPLEMENTACIÓN CONCRETA: PostgreSQL para inventario"""
    
    def __init__(self, connection_string: str):
        self._connection_string = connection_string
    
    async def get_current_inventory_levels(self) -> List[CacheInventoryLevel]:
        """SELECT de tu tabla shopify_inventory_level"""
        conn = await asyncpg.connect(self._connection_string)
        try:
            rows = await conn.fetch("""SELECT 
                                            sil.inventory_level_id, 
                                            sil.pos_sku, 
                                            sil.id_location,
                                            sil.shopify_inventory_level_gid,
                                            sil.quantities_available,
                                            sil.updated_at,
                                            sp.sync_op,
                                            sl.shopify_location_gid,
                                            sp.shopify_inventory_item_gid,
                                            sp.title,
                                            sp.price,
                                            sp.price_compare
                                        FROM shopify_inventory_level sil
                                        JOIN shopify_product sp on sil.pos_sku = sp.pos_sku
                                        JOIN shopify_location sl on sil.id_location = sl.id_location; 
                                        """)
            inventory_levels = []
            
            for row in rows:
                inventory_level = CacheInventoryLevel(
                    inventory_level_id=row['inventory_level_id'],
                    pos_sku=row['pos_sku'],
                    shopify_inventory_level_gid=row['shopify_inventory_level_gid'],
                    id_location=row['id_location'],
                    quantities_available=row['quantities_available'],
                    updated_at=row['updated_at'],  # Tu typo en la DB
                    sync_op=row['sync_op'],
                    shopify_location_gid=row['shopify_location_gid'],
                    shopify_inventory_item_gid=row['shopify_inventory_item_gid'],
                    price=row['price'],
                    price_compare=row['price_compare'],
                    title=row['title']
                )
                inventory_levels.append(inventory_level)
                #print(f"Producto Cache: {inventory_level.pos_sku} - {inventory_level.id_location} - {inventory_level.shopify_location_gid}")
            
            return inventory_levels
        finally:
            await conn.close()
    
    async def products_created_on_shopify(self, shopi_products: List[ShopiProduct]) -> None:
        """UPDATE gids del producto nuevo"""
        conn = await asyncpg.connect(self._connection_string)
        try:
            for shopi_product in shopi_products:
                await conn.execute("""
                    UPDATE shopify_product
                    SET shopify_product_gid = $1, 
                        shopify_variant_gid = $2, 
                        shopify_inventory_item_gid = $3,
                        sync_op='UPDATE'
                    WHERE pos_sku = $4;
                """, shopi_product.shopify_product_gid, shopi_product.shopify_variant_gid, shopi_product.shopify_inventory_item_gid, shopi_product.pos_sku)

                await conn.execute("""
                    UPDATE shopify_inventory_level
                    SET shopify_inventory_level_gid = $1
                    WHERE pos_sku = $2 and id_location = $3;
                """, shopi_product.shopify_inventory_level_gid, shopi_product.pos_sku, shopi_product.id_location)

        finally:
            await conn.close()
    
    async def update_inventory_level(self, updated_inv: List[ShopiProduct]) -> None:
        """UPDATE de tu tabla shopify_inventory_level"""
        conn = await asyncpg.connect(self._connection_string)
        try:
            for update in updated_inv:
                await conn.execute("""
                    UPDATE shopify_inventory_level 
                    SET quantities_available = $1
                    WHERE pos_sku = $2 AND id_location = $3;
                """, update.new_quantity, 
                    update.pos_sku, update.id_location)
        finally:
            await conn.close()