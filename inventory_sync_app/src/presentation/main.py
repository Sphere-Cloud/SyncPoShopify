from infrastructure.ERPDataExtractor import ERPDataExtractor
from infrastructure.PostgreSQLInventoryRepository import PostgreSQLInventoryRepository
from infrastructure.SmartChangeDetector import SmartChangeDetector
from infrastructure.ShopifyInventoryUpdater import ShopifyInventoryUpdater
from application.SyncInventoryUseCase import SyncInventoryUseCase
from infrastructure.PostgreSQLSyncLogRepository import PostgreSQLSyncLogRepository

import asyncio

async def main():
    """COMPOSICIÓN: Aquí se ensambla toda la aplicación"""
    
    # 1. CREAR IMPLEMENTACIONES CONCRETAS (INFRASTRUCTURE)
    erp_extractor = ERPDataExtractor(
        endpoint_url="http://beadcolors.myvnc.com/WSCatalogoPS/WSCatalogoPS/api/Articulos"
    )
    
    inventory_repo = PostgreSQLInventoryRepository(
        connection_string="postgresql://postgres:12345@localhost/POS_SYNC_SHOPI"
    )
    
    sync_log_repo = PostgreSQLSyncLogRepository(  # No implementé esta clase por brevedad
        connection_string="postgresql://postgres:12345@localhost/POS_SYNC_SHOPI"
    )
    
    change_detector = SmartChangeDetector()
    
    shopify_updater = ShopifyInventoryUpdater(
        shop_url="https://tu-tienda.myshopify.com",
        access_token="tu-access-token"
    )
    
    # 2. INYECTAR DEPENDENCIAS EN EL CASO DE USO (APPLICATION)
    sync_use_case = SyncInventoryUseCase(
        erp_extractor=erp_extractor,
        inventory_repo=inventory_repo,
        sync_log_repo=sync_log_repo,
        change_detector=change_detector,
        shopify_updater=shopify_updater
    )
    
    # 3. EJECUTAR EL CASO DE USO
    print("🚀 Iniciando sincronización ERP -> Shopify...")
    result = await sync_use_case.execute()
    
    print("\n📊 RESULTADO:")
    for key, value in result.items():
        print(f"   {key}: {value}")

# Ejecutar la aplicación
if __name__ == "__main__":
    asyncio.run(main())