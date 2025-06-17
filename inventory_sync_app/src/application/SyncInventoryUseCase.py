from domain.repositories.IERPDataExtractor import IERPDataExtractor
from domain.repositories.IInventoryLevelRepository import IInventoryLevelRepository
from domain.repositories.ISyncLogRepository import ISyncLogRepository
from domain.repositories.IChangeDetector import IChangeDetector
from domain.repositories.IShopifyUpdater import IShopifyUpdater

from typing import List, Optional, Dict, Any
from datetime import datetime

class SyncInventoryUseCase:
    """CASO DE USO PRINCIPAL: Sincronizar inventario ERP -> Shopify"""
    
    def __init__(
        self,
        erp_extractor: IERPDataExtractor,           # Dependencia inyectada
        inventory_repo: IInventoryLevelRepository,  # Dependencia inyectada
        sync_log_repo: ISyncLogRepository,          # Dependencia inyectada
        change_detector: IChangeDetector,           # Dependencia inyectada
        shopify_updater: IShopifyUpdater            # Dependencia inyectada
    ):
        # PRINCIPIO DE INVERSIÓN DE DEPENDENCIAS
        # El caso de uso depende de ABSTRACCIONES, no de implementaciones concretas
        self._erp_extractor = erp_extractor
        self._inventory_repo = inventory_repo
        self._sync_log_repo = sync_log_repo
        self._change_detector = change_detector
        self._shopify_updater = shopify_updater
    
    async def execute(self) -> Dict[str, Any]:
        """Ejecuta el caso de uso completo"""
        operation_start = datetime.now()
        
        try:
            # PASO 1: Extraer productos del ERP (12 segundos)
            print("🔄 Extrayendo productos del ERP...")
            erp_products = await self._erp_extractor.extract_products()
            print(f"✅ Extraídos {len(erp_products)} productos del ERP")
            
            # PASO 2: Obtener estado actual del inventario (PostgreSQL cache)
            print("🔄 Obteniendo inventario actual desde PostgreSQL...")
            current_inventory = await self._inventory_repo.get_current_inventory_levels()
            print(f"✅ Inventario actual: {len(current_inventory)} registros")
            
            # PASO 3: Detectar cambios (lógica de dominio)
            print("🔄 Detectando cambios de inventario...")
            changes = await self._change_detector.detect_inventory_changes(
                erp_products, current_inventory
            )
            print(f"✅ Detectados {len(changes)} cambios")
            
            # PASO 4: Filtrar cambios que valen la pena (reglas de negocio)
            worthy_changes = [change for change in changes if change.is_worth_updating()]
            print(f"✅ Cambios que valen la pena actualizar: {len(worthy_changes)}")
            
            # PASO 5: Actualizar Shopify (con rate limiting)
            if worthy_changes:
                print("🔄 Actualizando inventario en Shopify...")
                sync_results = await self._shopify_updater.update_inventory_batch(worthy_changes)
                
                # PASO 6: Guardar logs de sincronización
                for sync_result in sync_results:
                    await self._sync_log_repo.create_sync_log(sync_result)
                
                successful_updates = [r for r in sync_results if r.was_successful()]
                print(f"✅ Actualizaciones exitosas: {len(successful_updates)}/{len(sync_results)}")
            else:
                print("ℹ️ No hay cambios significativos para actualizar")
                sync_results = []
            
            # Resultado final
            operation_time = (datetime.now() - operation_start).total_seconds()
            return {
                "status": "SUCCESS",
                "operation_time_seconds": operation_time,
                "erp_products_extracted": len(erp_products),
                "changes_detected": len(changes),
                "changes_applied": len(sync_results),
                "successful_updates": len([r for r in sync_results if r.was_successful()])
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "operation_time_seconds": (datetime.now() - operation_start).total_seconds()
            }