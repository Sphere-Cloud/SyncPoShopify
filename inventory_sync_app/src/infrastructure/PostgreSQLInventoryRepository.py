from domain.repositories.IInventoryLevelRepository import IInventoryLevelRepository

from domain.entities.CacheInventoryLevel import CacheInventoryLevel

from typing import List, Optional, Dict, Any
from datetime import datetime

class PostgreSQLInventoryRepository(IInventoryLevelRepository):
    """IMPLEMENTACIÓN CONCRETA: PostgreSQL para inventario"""
    
    def __init__(self, connection_string: str):
        self._connection_string = connection_string
    
    async def get_current_inventory_levels(self) -> List[CacheInventoryLevel]:
        """SELECT de tu tabla shopify_inventory_level"""
        conn = await asyncpg.connect(self._connection_string)
        try:
            rows = await conn.fetch("SELECT * FROM shopify_inventory_level")
            inventory_levels = []
            
            for row in rows:
                inventory_level = CacheInventoryLevel(
                    inventory_level_id=row['inventory_level_id'],
                    pos_sku=row['pos_sku'],
                    shopify_inventory_level_gid=row['shopify_inventory_level_gid'],
                    location_name=row['location_name'],
                    quantities_available=row['quantities_available'],
                    updated_at=row['upadated_at']  # Tu typo en la DB
                )
                inventory_levels.append(inventory_level)
            
            return inventory_levels
        finally:
            await conn.close()
    
    async def update_inventory_level(self, inventory: CacheInventoryLevel) -> None:
        """UPDATE de tu tabla shopify_inventory_level"""
        conn = await asyncpg.connect(self._connection_string)
        try:
            await conn.execute("""
                UPDATE shopify_inventory_level 
                SET quantities_available = $1, upadated_at = $2
                WHERE pos_sku = $3 AND location_name = $4
            """, inventory.quantities_available, datetime.now(), 
                inventory.pos_sku, inventory.location_name)
        finally:
            await conn.close()