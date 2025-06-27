from domain.repositories.ISyncLogRepository import ISyncLogRepository

from domain.entities.ProductSyncLog import ProductSyncLog

from typing import List
import asyncpg

class PostgreSQLSyncLogRepository(ISyncLogRepository):
    """ IMPLEMENTACION CONCRETA: PostgreSQL para inventario """

    def __init__(self, connection_string: str):
        self._connection_string = connection_string

    async def create_sync_logs(self, sync_logs: List[ProductSyncLog]) -> None:
        conn = await asyncpg.connect(self._connection_string)

        try:
            for sync_log in sync_logs:
                await conn.execute("""
                    INSERT INTO product_sync_log
                    (pos_sku, sync_info, before_sync, after_sync, synced_status, sync_type)
                    VALUES ($1,$2,$3,$4,$5,$6)               
                """, 
                sync_log.sku_pos, 
                sync_log.sync_info, 
                sync_log.before_sync, 
                sync_log.after_sync, 
                sync_log.synced_status, 
                sync_log.sync_type)

        finally:
            await conn.close()

    
    


