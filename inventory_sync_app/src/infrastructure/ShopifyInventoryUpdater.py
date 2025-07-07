from domain.repositories.IShopifyUpdater import IShopifyUpdater
from domain.entities.InventoryChange import InventoryChange
from domain.entities.ProductSyncLog import ProductSyncLog
from domain.entities.ShopiProduct import ShopiProduct

import math
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
import asyncio
import logging

class ShopifyInventoryUpdater(IShopifyUpdater):
    """IMPLEMENTACIÓN CONCRETA: Actualiza inventario en Shopify"""
    
    def __init__(self, shop_url: str, access_token: str, timeout: int = 30):
        self._shop_url = shop_url
        self._access_token = access_token
        self._timeout = timeout  # ✅ AGREGADO: Faltaba inicializar timeout
        self._rate_limit_calls = 0
        self._rate_limit_max = 40  # Por segundo
    
    async def update_inventory_batch(self, changes: List[InventoryChange]) -> List[List[Any]]:
        """Actualiza inventario respetando rate limits"""
        sync_results = []
        sync_update_db = []
        
        for change in changes:
            
            
            try:
                success = None
                sync_op = change.sync_op
                sync_res = ""

                if sync_op == "UPDATE":
                    success = await self._update_single_inventory(change)
                    sync_res = f"Updated from {change.old_quantity} to {change.new_quantity}"

                if not success:
                    sync_res = f"Failed to {sync_op}"
                
                
                sync_log = ProductSyncLog(
                    sync_id=0, 
                    sku_pos=change.sku, 
                    sync_info=sync_res,  
                    before_sync=change.old_quantity,  
                    after_sync=change.new_quantity,   
                    synced_at=datetime.now(),
                    synced_status="SUCCESS" if success else "FAILED",
                    sync_type=sync_op
                )
                sync_results.append(sync_log)
                
                sync_update_db.append(success)
                
                
                
            except Exception as e:
                sync_log = ProductSyncLog(
                    sync_id=0,
                    sku_pos=change.sku,
                    sync_info=f"Error: {str(e)}",
                    before_sync=change.old_quantity,
                    after_sync=change.new_quantity,
                    synced_at=datetime.now(),
                    synced_status="FAILED",
                    sync_type=change.sync_op
                )
                sync_results.append(sync_log)
            
            await asyncio.sleep(4)  # Esperar 1 segundo
        
        return [sync_results, sync_update_db]
    
    async def create_inventory_batch(self, changes: List[InventoryChange]) -> List[List[Any]]:
        """Crear los productos nuevos en shopify respetando rate limits"""
        sync_results = []
        sync_update_db = []

        for change in changes:

            try:
                sync_op = change.sync_op
                success = None
                sync_res = ""

                if sync_op == "CREATE":
                    success = await self._create_single_inventory(change)
                    sync_res = f"Create from {change.old_quantity} to {change.new_quantity}"
                
                if success == None:
                    sync_res = f"Failed to {sync_op}"
                

                sync_log = ProductSyncLog(
                    sync_id=0, 
                    sku_pos=change.sku, 
                    sync_info=sync_res,  
                    before_sync=change.old_quantity,  
                    after_sync=change.new_quantity,   
                    synced_at=datetime.now(),
                    synced_status="SUCCESS" if success else "FAILED",
                    sync_type=sync_op
                )
                sync_results.append(sync_log)
                sync_update_db.append(success)

                

            except Exception as e:
                sync_log = ProductSyncLog(
                    sync_id=0,
                    sku_pos=change.sku,
                    sync_info=f"Error: {str(e)}",
                    before_sync=change.old_quantity,
                    after_sync=change.new_quantity,
                    synced_at=datetime.now(),
                    synced_status="FAILED",
                    sync_type=change.sync_op
                )
                sync_results.append(sync_log)

            await asyncio.sleep(4)  # Esperar 1 segundo

        return [sync_results, sync_update_db]
    
    async def _update_single_inventory(self, change: InventoryChange) -> bool:
        """Llamada real a Shopify API para actualizar inventario"""
        shopi_product = ShopiProduct(pos_sku=change.sku,id_location=change.id_location, new_quantity=int(math.ceil(change.new_quantity)))
        try:
            payload = {
                "query": "mutation InventorySet($input: InventorySetQuantitiesInput!) { inventorySetQuantities(input: $input) { inventoryAdjustmentGroup { createdAt reason referenceDocumentUri changes { name delta } } userErrors { field message } } }",
                "variables": {
                    "input": {
                        "ignoreCompareQuantity": True,
                        "name": "available",
                        "reason": "movement_updated",
                        "quantities": [{
                            "inventoryItemId": change.shopify_inventory_item,  
                            "locationId": change.shopify_location_gid,  
                            "quantity": int(change.new_quantity)  
                        }]
                    }
                }
            }

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Shopify-Access-Token': self._access_token
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
                async with session.post(self._shop_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Update inventory failed: {response.status} - {response.reason}")
                    
                    data = await response.json()
                    
                    print("Update Data: ", data)
                    
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    user_errors = data.get('data', {}).get('inventorySetQuantities', {}).get('userErrors', [])
                    if user_errors:
                        raise Exception(f"User errors: {user_errors}")
                    
                    return shopi_product
                    
        except Exception as e:
            return shopi_product
    
    async def _create_single_inventory(self, change: InventoryChange) -> bool:
        """Llamada real a Shopify API para crear producto e inventario"""

        shopi_product = ShopiProduct(pos_sku=change.sku,id_location=change.id_location)

        try:
            
            

            # 1. Crear producto
            payloadCreateProduct = {
                "query": "mutation ProductCreate($product: ProductCreateInput!) { productCreate(product: $product) { product { id variants(first: 10) { edges { node { id inventoryItem { id tracked inventoryLevels(first: 6) { edges { node { id location { name } quantities(names: \"available\") { name quantity } } } } } } } } } } }",
                "variables": {
                    "product": {
                        "title": change.title,  
                        "status": "ACTIVE"
                    }
                }
            }

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Shopify-Access-Token': self._access_token
            }

            # Crear producto
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
                async with session.post(self._shop_url, json=payloadCreateProduct, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Create Product failed: {response.status} - {response.reason}")
                    
                    data = await response.json()
                    print("Create:", data)
                    
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    product_data = data['data']['productCreate']['product']
                    shopi_product.shopify_product_gid = product_data['id']
                    shopi_product.shopify_variant_gid = product_data['variants']['edges'][0]['node']['id']
                    shopi_product.shopify_inventory_item_gid = product_data['variants']['edges'][0]['node']['inventoryItem']['id']

            # 2. Habilitar tracking de inventario
            payloadVariantBulkUpdate = {
                "query": "mutation ProductVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) { productVariantsBulkUpdate(productId: $productId, variants: $variants) { product { id } productVariants { id inventoryItem{ id tracked } } userErrors { field message } } }",
                "variables": {
                    "productId": shopi_product.shopify_product_gid,
                    "variants": [{
                        "id": shopi_product.shopify_variant_gid,
                        "price": change.price,
                        "inventoryItem": {
                            "tracked": True,
                            "sku": change.sku
                        }
                    }]
                }
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
                async with session.post(self._shop_url, json=payloadVariantBulkUpdate, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Update Inventory tracking failed: {response.status} - {response.reason}")
                    
                    data = await response.json()
                    print("Activate Variant Info:", data)
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")

            # 3. Activar inventario en ubicación
            payloadActivateInventoryItem = {
                "query": "mutation ActivateInventoryItem($inventoryItemId: ID!, $locationId: ID!, $available: Int) { inventoryActivate(inventoryItemId: $inventoryItemId, locationId: $locationId, available: $available) { inventoryLevel { id quantities(names: [\"available\"]) { name quantity } item { id } location { id } } } }",
                "variables": {
                    "inventoryItemId": shopi_product.shopify_inventory_item_gid,
                    "locationId": change.shopify_location_gid,  
                    "available": 1  
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
                async with session.post(self._shop_url, json=payloadActivateInventoryItem, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Activate Inventory failed: {response.status} - {response.reason}")
                    
                    data = await response.json()
                    print("Activate Location: ", data)
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    shopi_product.shopify_inventory_level_gid = data['data']['inventoryActivate']['inventoryLevel']['id']

            # 4. Establecer cantidad final
            payloadInventorySet = {
                "query": "mutation InventorySet($input: InventorySetQuantitiesInput!) { inventorySetQuantities(input: $input) { inventoryAdjustmentGroup { createdAt reason referenceDocumentUri changes { name delta } } userErrors { field message } } }",
                "variables": {
                    "input": {
                        "ignoreCompareQuantity": True,
                        "name": "available",
                        "reason": "movement_updated",
                        "quantities": [{
                            "inventoryItemId": shopi_product.shopify_inventory_item_gid,
                            "locationId": change.shopify_location_gid,  
                            "quantity": int(change.new_quantity)  
                        }]
                    }
                }
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
                async with session.post(self._shop_url, json=payloadInventorySet, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Inventory Set failed: {response.status} - {response.reason}")
                    
                    data = await response.json()
                    print("Update Quantities", data)
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    user_errors = data.get('data', {}).get('inventorySetQuantities', {}).get('userErrors', [])
                    if user_errors:
                        raise Exception(f"User errors: {user_errors}")

            # ✅ AGREGADO: Guardar el producto creado en la base de datos
            # Aquí deberías llamar a tu repositorio para guardar shopi_product
            # await self._product_repository.save(shopi_product)
            
            return shopi_product

        except Exception as e:
            return shopi_product