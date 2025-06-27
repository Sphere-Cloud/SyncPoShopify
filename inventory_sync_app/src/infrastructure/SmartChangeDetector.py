from domain.repositories.IChangeDetector import IChangeDetector

from domain.entities.ERPProduct import ERPProduct
from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.InventoryChange import InventoryChange

from typing import List, Optional, Dict, Any
from decimal import Decimal
import math

class SmartChangeDetector(IChangeDetector):
    """IMPLEMENTACIÓN CONCRETA: Detecta cambios inteligentemente"""
    
    async def detect_inventory_changes(
        self, 
        erp_products: List[ERPProduct],
        current_inventory: List[CacheInventoryLevel]
    ) -> List[InventoryChange]:
        """Compara ERP vs estado actual y detecta cambios"""
        changes = []
        

        locations = [1]
        
        # Crear un diccionario para búsqueda rápida
        inventory_by_sku = {f"{inv.pos_sku}-{inv.id_location}": inv for inv in current_inventory}
        
        
        for erp_product in erp_products:
            for location in locations:

                sku = erp_product.codigo
                new_quantity = erp_product.existencia

                code = f"{sku}-{location}"
                
                if code in inventory_by_sku:

                    current_inv = inventory_by_sku[code]
                    old_quantity = current_inv.quantities_available
                    
                    # APLICAR REGLAS DE NEGOCIO DE LA ENTIDAD
                    if current_inv.should_update(new_quantity) or current_inv.is_new_product():
                        priority = 1 if current_inv.is_critical_change(new_quantity) else 3
                        
                        change = InventoryChange(
                            sku=sku,
                            id_location=current_inv.id_location,
                            old_quantity=old_quantity,
                            new_quantity=new_quantity,
                            priority=priority,
                            estimated_cost=Decimal('0.01'),  # Costo por API call
                            sync_op="CREATE" if current_inv.sync_op == "CREATE" else "UPDATE",
                            shopify_inventory_item=current_inv.shopify_inventory_item_gid,
                            title=current_inv.title,
                            price=current_inv.price,
                            price_compare=current_inv.price_compare,
                            shopify_location_gid=current_inv.shopify_location_gid
                        )
                        changes.append(change)

                        print(f"Product Change {change.sku}:  Old Quantity {math.ceil(change.old_quantity)} New Quantity: {math.ceil(change.new_quantity)} ")
        
        # Ordenar por prioridad (críticos primero)
        changes.sort(key=lambda x: x.priority)
        return changes