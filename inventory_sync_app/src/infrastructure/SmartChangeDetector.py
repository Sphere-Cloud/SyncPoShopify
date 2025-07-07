from domain.repositories.IChangeDetector import IChangeDetector
from domain.entities.KordataProduct import KordataProduct
from domain.entities.CacheInventoryLevel import CacheInventoryLevel
from domain.entities.InventoryChange import InventoryChange

from typing import List, Optional, Dict, Any
from decimal import Decimal
import math
import json
import os
import csv
from datetime import datetime

class SmartChangeDetector(IChangeDetector):
    """IMPLEMENTACIÓN CONCRETA: Detecta cambios inteligentemente"""
    
    async def detect_inventory_changes(
        self, 
        erp_products: List[KordataProduct],
        current_inventory: List[CacheInventoryLevel]
    ) -> List[InventoryChange]:
        """Compara ERP vs estado actual y detecta cambios"""
        changes = []
        
        # Crear un diccionario para búsqueda rápida
        inventory_by_sku = {f"{inv.pos_sku}-{inv.id_location}": inv for inv in current_inventory}
        
        print(f"Total inventory items: {len(inventory_by_sku)}")
        print("Sample inventory keys:", list(inventory_by_sku.keys())[:5])
        
        # OPCIÓN 1: Si el ERP product ya tiene la ubicación definida
        for erp_product in erp_products:
            # Suponiendo que el producto ERP tiene información de ubicación
            # Necesitas mapear el almacen del ERP a id_location
            location_id = self._map_almacen_to_location(erp_product.almacen)
            
            if location_id is None:
                #print(f"No se pudo mapear almacen '{erp_product.almacen}' para SKU {erp_product.sku}")
                continue
                
            sku = erp_product.sku
            new_quantity = erp_product.existencia
            code = f"{sku}-{location_id}"
            
            print(f"Buscando: {code}")
            
            if code in inventory_by_sku:
                current_inv = inventory_by_sku[code]
                old_quantity = current_inv.quantities_available
                
                print(f"Encontrado {code}: old={old_quantity}, new={new_quantity}")
                
                # APLICAR REGLAS DE NEGOCIO DE LA ENTIDAD
                if current_inv.should_update(new_quantity) or current_inv.is_new_product():
                    priority = 1 if current_inv.is_critical_change(new_quantity) else 3
                    
                    change = InventoryChange(
                        sku=sku,
                        id_location=current_inv.id_location,
                        old_quantity=old_quantity,
                        new_quantity=new_quantity,
                        priority=priority,
                        estimated_cost=Decimal('0.01'),
                        sync_op="CREATE" if current_inv.sync_op == "CREATE" else "UPDATE",
                        shopify_inventory_item=current_inv.shopify_inventory_item_gid,
                        title=current_inv.title,
                        price=current_inv.price,
                        price_compare=current_inv.price_compare,
                        shopify_location_gid=current_inv.shopify_location_gid
                    )
                    changes.append(change)
                    print(f"Change detected for {change.sku}: {old_quantity} -> {new_quantity}")
            else:
                print(f"No encontrado en cache: {code}")
        
        
        print(f"Total changes detected: {len(changes)}")
        
        # Ordenar por prioridad (críticos primero)
        changes.sort(key=lambda x: x.priority)
        
        # Guardar cambios en JSON
        self.save_changes_to_json(changes)
        self.save_changes_to_csv(changes)
        
        return changes
    
    def _map_almacen_to_location(self, almacen: str) -> Optional[int]:
        """Mapea el nombre del almacén del ERP a id_location"""
        # Define tu mapeo según tu lógica de negocio
        almacen_mapping = {
            "CEDIS": 1,
            "COACALCO": 2,
            "PUEBLA": 3,
            "QUERETARO": 4,
            "LOS REYES": 5,
            "TIJUANA": 6,
            "TOLUCA": 7,
            "TOREO/PERICENTRO": 8,
            "EJE CENTRAL": 9
        }
        
        if not almacen:
            return None  # Default location si no hay almacén definido
            
        # Búsqueda case-insensitive
        almacen_upper = almacen.upper().strip()
        
        for key, location_id in almacen_mapping.items():
            if key.upper() in almacen_upper or almacen_upper in key.upper():
                return location_id
        
        # Si no encuentra mapeo, usar ubicación por defecto
        print(f"Almacén no mapeado: '{almacen}', usando ubicación por defecto (None)")
        return None

    def save_changes_to_json(self, changes: List[InventoryChange], filename: str = None) -> str:
        """
        Guarda la información de los cambios en un archivo JSON
        
        Args:
            changes: Lista de cambios de inventario
            filename: Nombre del archivo (opcional). Si no se proporciona, se genera automáticamente
            
        Returns:
            str: Ruta del archivo guardado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_changes_{timestamp}.json"
        
        # Crear directorio si no existe
        os.makedirs("logs/inventory_changes", exist_ok=True)
        filepath = os.path.join("logs/inventory_changes", filename)
        
        # Convertir los cambios a formato serializable
        changes_data = []
        for change in changes:
            change_dict = {
                "sku": change.sku,
                "id_location": change.id_location,
                "old_quantity": float(change.old_quantity) if change.old_quantity is not None else None,
                "new_quantity": float(change.new_quantity) if change.new_quantity is not None else None,
                "quantity_difference": float(change.new_quantity - change.old_quantity) if change.old_quantity is not None and change.new_quantity is not None else None,
                "priority": change.priority,
                "estimated_cost": float(change.estimated_cost) if change.estimated_cost is not None else None,
                "sync_op": change.sync_op,
                "shopify_inventory_item": change.shopify_inventory_item,
                "title": change.title,
                "price": float(change.price) if change.price is not None else None,
                "price_compare": float(change.price_compare) if change.price_compare is not None else None,
                "shopify_location_gid": change.shopify_location_gid,
                "timestamp": datetime.now().isoformat()
            }
            changes_data.append(change_dict)
        
        # Crear estructura del JSON con metadata
        json_data = {
            "metadata": {
                "total_changes": len(changes),
                "generated_at": datetime.now().isoformat(),
                "critical_changes": len([c for c in changes if c.priority == 1]),
                "normal_changes": len([c for c in changes if c.priority == 3]),
                "create_operations": len([c for c in changes if c.sync_op == "CREATE"]),
                "update_operations": len([c for c in changes if c.sync_op == "UPDATE"])
            },
            "changes": changes_data
        }
        
        # Guardar archivo JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Cambios guardados en: {filepath}")
            print(f"📊 Total de cambios: {len(changes)}")
            print(f"🔴 Cambios críticos: {json_data['metadata']['critical_changes']}")
            print(f"🟡 Cambios normales: {json_data['metadata']['normal_changes']}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error al guardar archivo JSON: {str(e)}")
            return None
    
    def save_changes_to_csv(self, changes: List[InventoryChange], filename: str = None) -> str:
        """
        Guarda la información de los cambios en un archivo CSV
        
        Args:
            changes: Lista de cambios de inventario
            filename: Nombre del archivo (opcional). Si no se proporciona, se genera automáticamente
            
        Returns:
            str: Ruta del archivo guardado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_changes_{timestamp}.csv"
        
        # Crear directorio si no existe
        os.makedirs("logs/inventory_changes", exist_ok=True)
        filepath = os.path.join("logs/inventory_changes", filename)
        
        # Definir las columnas del CSV
        csv_columns = [
            'sku',
            'id_location',
            'old_quantity',
            'new_quantity',
            'quantity_difference',
            'priority',
            'priority_description',
            'estimated_cost',
            'sync_op',
            'shopify_inventory_item',
            'title',
            'price',
            'price_compare',
            'shopify_location_gid',
            'timestamp'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                
                # Escribir encabezados
                writer.writeheader()
                
                # Escribir datos de cambios
                for change in changes:
                    quantity_diff = None
                    if change.old_quantity is not None and change.new_quantity is not None:
                        quantity_diff = float(change.new_quantity - change.old_quantity)
                    
                    priority_desc = "Crítico" if change.priority == 1 else "Normal"
                    
                    row_data = {
                        'sku': change.sku,
                        'id_location': change.id_location,
                        'old_quantity': float(change.old_quantity) if change.old_quantity is not None else None,
                        'new_quantity': float(change.new_quantity) if change.new_quantity is not None else None,
                        'quantity_difference': quantity_diff,
                        'priority': change.priority,
                        'priority_description': priority_desc,
                        'estimated_cost': float(change.estimated_cost) if change.estimated_cost is not None else None,
                        'sync_op': change.sync_op,
                        'shopify_inventory_item': change.shopify_inventory_item,
                        'title': change.title,
                        'price': float(change.price) if change.price is not None else None,
                        'price_compare': float(change.price_compare) if change.price_compare is not None else None,
                        'shopify_location_gid': change.shopify_location_gid,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    writer.writerow(row_data)
            
            print(f"📊 Cambios guardados en CSV: {filepath}")
            print(f"📋 Columnas incluidas: {len(csv_columns)}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error al guardar archivo CSV: {str(e)}")
            return None


# VERSIÓN ALTERNATIVA: Con debugging más detallado
class SmartChangeDetectorDebug(IChangeDetector):
    """Versión con debugging extenso para identificar problemas"""
    
    async def detect_inventory_changes(
        self, 
        erp_products: List[KordataProduct],
        current_inventory: List[CacheInventoryLevel]
    ) -> List[InventoryChange]:
        
        changes = []
        
        # Debugging inicial
        print(f"\n=== DEBUGGING CHANGE DETECTION ===")
        print(f"ERP Products: {len(erp_products)}")
        print(f"Cache Inventory: {len(current_inventory)}")
        
        # Analizar estructura de datos
        if erp_products:
            sample_erp = erp_products[0]
            print(f"Sample ERP Product: SKU={sample_erp.sku}, Almacen={sample_erp.almacen}, Existencia={sample_erp.existencia}")
        
        if current_inventory:
            sample_cache = current_inventory[0]
            print(f"Sample Cache: SKU={sample_cache.pos_sku}, Location={sample_cache.id_location}, Qty={sample_cache.quantities_available}")
        
        # Crear diccionario de inventario
        inventory_by_sku = {f"{inv.pos_sku}-{inv.id_location}": inv for inv in current_inventory}
        
        # Mostrar algunas claves del cache
        print(f"Cache keys sample: {list(inventory_by_sku.keys())[:10]}")
        
        # Analizar cada producto ERP
        for i, erp_product in enumerate(erp_products):
            print(f"\n--- Processing ERP Product {i+1}/{len(erp_products)} ---")
            print(f"SKU: {erp_product.sku}")
            print(f"Almacen: {erp_product.almacen}")
            print(f"Existencia: {erp_product.existencia}")
            
            # Buscar este SKU en todas las ubicaciones del cache
            found_locations = []
            for key, cache_item in inventory_by_sku.items():
                if cache_item.pos_sku == erp_product.sku:
                    found_locations.append((cache_item.id_location, cache_item.quantities_available))
            
            print(f"Found in cache at locations: {found_locations}")
            
            if not found_locations:
                print(f"❌ SKU {erp_product.sku} NOT FOUND in cache at all")
                continue
            
            # Procesar cambios para ubicaciones encontradas
            location_id = self._map_almacen_to_location(erp_product.almacen)
            code = f"{erp_product.sku}-{location_id}"
            
            if code in inventory_by_sku:
                current_inv = inventory_by_sku[code]
                old_quantity = current_inv.quantities_available
                new_quantity = erp_product.existencia
                
                print(f"✅ Match found: {code}")
                print(f"   Old quantity: {old_quantity}")
                print(f"   New quantity: {new_quantity}")
                print(f"   Difference: {new_quantity - old_quantity}")
                
                # Verificar si debe actualizar
                should_update = current_inv.should_update(new_quantity) or current_inv.is_new_product()
                print(f"   Should update: {should_update}")
                
                if should_update:
                    priority = 1 if current_inv.is_critical_change(new_quantity) else 3
                    
                    change = InventoryChange(
                        sku=erp_product.sku,
                        id_location=current_inv.id_location,
                        old_quantity=old_quantity,
                        new_quantity=new_quantity,
                        priority=priority,
                        estimated_cost=Decimal('0.01'),
                        sync_op="CREATE" if current_inv.sync_op == "CREATE" else "UPDATE",
                        shopify_inventory_item=current_inv.shopify_inventory_item_gid,
                        title=current_inv.title,
                        price=current_inv.price,
                        price_compare=current_inv.price_compare,
                        shopify_location_gid=current_inv.shopify_location_gid
                    )
                    changes.append(change)
                    print(f"   ✅ CHANGE DETECTED!")
                else:
                    print(f"   ⚠️  No change needed (business rule)")
            else:
                print(f"❌ Code {code} not found in cache")
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total changes detected: {len(changes)}")
        
        changes.sort(key=lambda x: x.priority)
        
        # Guardar cambios en JSON
        self.save_changes_to_json(changes)
        
        return changes
    
    def _map_almacen_to_location(self, almacen: str) -> int:
        """Mapeo simple para debugging"""
        return 7  # Usar ubicación 7 como en tu ejemplo

    def save_changes_to_json(self, changes: List[InventoryChange], filename: str = None) -> str:
        """
        Guarda la información de los cambios en un archivo JSON
        
        Args:
            changes: Lista de cambios de inventario
            filename: Nombre del archivo (opcional). Si no se proporciona, se genera automáticamente
            
        Returns:
            str: Ruta del archivo guardado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_changes_debug_{timestamp}.json"
        
        # Crear directorio si no existe
        os.makedirs("logs/inventory_changes", exist_ok=True)
        filepath = os.path.join("logs/inventory_changes", filename)
        
        # Convertir los cambios a formato serializable
        changes_data = []
        for change in changes:
            change_dict = {
                "sku": change.sku,
                "id_location": change.id_location,
                "old_quantity": float(change.old_quantity) if change.old_quantity is not None else None,
                "new_quantity": float(change.new_quantity) if change.new_quantity is not None else None,
                "quantity_difference": float(change.new_quantity - change.old_quantity) if change.old_quantity is not None and change.new_quantity is not None else None,
                "priority": change.priority,
                "estimated_cost": float(change.estimated_cost) if change.estimated_cost is not None else None,
                "sync_op": change.sync_op,
                "shopify_inventory_item": change.shopify_inventory_item,
                "title": change.title,
                "price": float(change.price) if change.price is not None else None,
                "price_compare": float(change.price_compare) if change.price_compare is not None else None,
                "shopify_location_gid": change.shopify_location_gid,
                "timestamp": datetime.now().isoformat()
            }
            changes_data.append(change_dict)
        
        # Crear estructura del JSON con metadata
        json_data = {
            "metadata": {
                "total_changes": len(changes),
                "generated_at": datetime.now().isoformat(),
                "critical_changes": len([c for c in changes if c.priority == 1]),
                "normal_changes": len([c for c in changes if c.priority == 3]),
                "create_operations": len([c for c in changes if c.sync_op == "CREATE"]),
                "update_operations": len([c for c in changes if c.sync_op == "UPDATE"]),
                "debug_mode": True
            },
            "changes": changes_data
        }
        
        # Guardar archivo JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Cambios guardados en: {filepath}")
            print(f"📊 Total de cambios: {len(changes)}")
            print(f"🔴 Cambios críticos: {json_data['metadata']['critical_changes']}")
            print(f"🟡 Cambios normales: {json_data['metadata']['normal_changes']}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error al guardar archivo JSON: {str(e)}")
            return None