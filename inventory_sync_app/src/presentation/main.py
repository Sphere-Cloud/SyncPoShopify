from infrastructure.ERPDataExtractor import ERPDataExtractor
from infrastructure.PostgreSQLInventoryRepository import PostgreSQLInventoryRepository
from infrastructure.SmartChangeDetector import SmartChangeDetector
from infrastructure.ShopifyInventoryUpdater import ShopifyInventoryUpdater
from application.SyncInventoryUseCase import SyncInventoryUseCase
from infrastructure.PostgreSQLSyncLogRepository import PostgreSQLSyncLogRepository

from shared.config.config_manager import ApplicationConfig, get_config
from shared.logging.logging_setup import setup_logging

import asyncio

async def main(config: ApplicationConfig = None):
    """COMPOSICIÓN: Aquí se ensambla toda la aplicación"""
    
    if config is None:
        config = get_config()


    
    # 1. CREAR IMPLEMENTACIONES CONCRETAS (INFRASTRUCTURE)
    erp_extractor = ERPDataExtractor(
        endpoint_url=config.erp.endpoint_url,
        bearer_token=config.erp.api_key
    )
    
    inventory_repo = PostgreSQLInventoryRepository(
        connection_string=f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}/{config.database.name}"
    )
    
    sync_log_repo = PostgreSQLSyncLogRepository(  # No implementé esta clase por brevedad
        connection_string=f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}/{config.database.name}"
    )
    
    change_detector = SmartChangeDetector()
    
    shopify_updater = ShopifyInventoryUpdater(
        shop_url=config.shopify.shop_domain,
        access_token=config.shopify.access_token
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