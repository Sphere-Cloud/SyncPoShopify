from domain.repositories.IChangeDetector import IChangeDetector

from domain.entities.ERPProduct import ERPProduct
from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.InventoryChange import InventoryChange

from typing import List, Optional, Dict, Any
from decimal import Decimal

class SmartChangeDetector(IChangeDetector):
    """IMPLEMENTACIÓN CONCRETA: Detecta cambios inteligentemente"""
    
    async def detect_inventory_changes(
        self, 
        erp_products: List[ERPProduct],
        current_inventory: List[CacheInventoryLevel]
    ) -> List[InventoryChange]:
        """Compara ERP vs estado actual y detecta cambios"""
        changes = []
        

        locations = ["default"]
        
        # Crear un diccionario para búsqueda rápida
        inventory_by_sku = {f"{inv.pos_sku}{inv.location_name}": inv for inv in current_inventory}
        
        
        for erp_product in erp_products:
            for location in locations:

                sku = erp_product.codigo
                new_quantity = erp_product.existencia

                code = f"{sku}{location}"
                
                if code in inventory_by_sku:

                    current_inv = inventory_by_sku[code]
                    old_quantity = current_inv.quantities_available
                    
                    # APLICAR REGLAS DE NEGOCIO DE LA ENTIDAD
                    if current_inv.needs_inventory_update(new_quantity):
                        priority = 1 if current_inv.is_critical_change(new_quantity) else 3
                        
                        change = InventoryChange(
                            sku=sku,
                            location_name=current_inv.location_name,
                            old_quantity=old_quantity,
                            new_quantity=new_quantity,
                            priority=priority,
                            estimated_cost=Decimal('0.01')  # Costo por API call
                        )
                        changes.append(change)

                        print(f"Product Change {change.sku}:  Old Quantity {change.old_quantity} New Quantity: {change.new_quantity} ")
        
        # Ordenar por prioridad (críticos primero)
        changes.sort(key=lambda x: x.priority)
        return changes