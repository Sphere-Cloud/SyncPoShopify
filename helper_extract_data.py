#!/usr/bin/env python3

import asyncio
import aiohttp
import json
from datetime import datetime


has_next_page = True
end_cursor = None

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Shopify-Access-Token': 
}

locations = {
    "CEDIS/Envio Nacional": 1,
    "PT Coacalco": 2,
    "PT Puebla": 3,
    "PT Querétaro": 4,
    "PT Reyes/La Paz": 5,
    "PT Tijuana": 6,
    "PT Toluca": 7,
    "PT Toreo/Pericentro": 8,
    "Eje Central": 9
}

all_products = []

async def getInfo():
    global has_next_page, end_cursor
    
    while has_next_page:
        payload = {
            "query": "query GetProducts($numProducts: Int!, $cursor: String) { products(first: $numProducts, after: $cursor) { nodes { id title category{ name } variants(first:10){ edges{ node{ id sku price compareAtPrice inventoryItem{ id tracked inventoryLevels(first:20){ edges{ node{ id location{ id name } quantities(names: \"available\") { name quantity } } } } } } } } } pageInfo{ hasPreviousPage hasNextPage startCursor endCursor } } }",
            "variables": {
                "numProducts": 100,
                "cursor": end_cursor
            }
        }

        payloadExact = {
            "query": "query GetProducts($numProducts: Int!, $cursor: String) { products(first: $numProducts, after: $cursor) { nodes { id title category { name } variants(first: 10) { edges { node { id sku price compareAtPrice inventoryItem { id tracked inventoryLevel(locationId: \"gid://shopify/Location/107999363362\"){ id location{ id name } quantities(names: \"available\"){ name quantity } } } } } } } pageInfo { hasPreviousPage hasNextPage startCursor endCursor } } }",
            "variables": {
                "numProducts": 100,
                "cursor": end_cursor
            }
        }

        payloadExactProduct = {
            "query": "query GetProductVariants { product(id: \"gid://shopify/Product/9760129351970\") { id title category { name } variants(first: 10) { edges { node { id sku price compareAtPrice inventoryItem { id tracked inventoryLevels(first:20){ edges{ node{ id location{ id name } quantities(names: \"available\"){ name quantity } } } } } } } } } }",
            "variables": { }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('https://xxxx.myshopify.com/admin/api/2025-07/graphql.json', 
                                      json=payloadExactProduct, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Retrieve Information Failed: {response.status} - {response.reason}")

                    data = await response.json()

                    #print(data)
                    
                    if 'errors' in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    
                    # has_next_page = data['data']['products']['pageInfo']['hasNextPage']
                    # end_cursor = data['data']['products']['pageInfo']['endCursor']
                    # product_data = data['data']['products']['nodes']

                    has_next_page = False

                    product_data = [data['data']['product']]

                    for product in product_data:
                        print(product)
                        PRODUCT_GID = product['id']
                        TITLE = product['title']
                        CATEGORY = product['category']['name'] if product['category'] is not None else ""
                        variants = product['variants']['edges']

                        for variant in variants:
                            variant_node = variant['node']
                            VARIANT_GID = variant_node['id']
                            SKU = variant_node['sku']
                            PRICE = float(variant_node['price']) if variant_node['price'] else 0.0
                            PRICE_COMPARE_AT = float(variant_node['compareAtPrice']) if variant_node['compareAtPrice'] else 0.0
                            INVENTORY_ITEM_GID = variant_node['inventoryItem']['id']

                            if variant_node['inventoryItem']['tracked']:

                                # inventoryLevel = variant_node['inventoryItem']['inventoryLevel']
                                # INVENTORY_LEVEL_GID = inventoryLevel['id']
                                # location_name = inventoryLevel['location']['name']

                                # if location_name in locations:
                                #     LOCATION = locations[location_name]
                                #     QUANTITIES_AVAILABLE = inventoryLevel['quantities'][0]['quantity']

                                #     info = {
                                #             "SKU": SKU,
                                #             "TITLE": TITLE,
                                #             "PRICE": PRICE,
                                #             "PRICECOMPAREAT": PRICE_COMPARE_AT,
                                #             "CATEGORY": CATEGORY,
                                #             "SYNC_OP": "UPDATE",
                                #             "SHOPIFY_PRODUCT_GID": PRODUCT_GID,
                                #             "SHOPIFY_VARIANT_GID": VARIANT_GID,
                                #             "SHOPIFY_INVENTORY_ITEM_GID": INVENTORY_ITEM_GID,
                                #             "ID_LOCATION": LOCATION,
                                #             "SHOPIFY_INVENTORY_LEVEL_GID": INVENTORY_LEVEL_GID,
                                #             "QUANTITIES_AVAILABLE": QUANTITIES_AVAILABLE 
                                #         }

                                #     all_products.append(info)
                            


                                inventoryLevels = variant_node['inventoryItem']['inventoryLevels']['edges']

                                for level in inventoryLevels:
                                    level_node = level['node']
                                    INVENTORY_LEVEL_GID = level_node['id']
                                    location_name = level_node['location']['name']
                                    
                                    # Verificar si la ubicación existe en nuestro diccionario
                                    if location_name in locations:
                                        LOCATION = locations[location_name]
                                        QUANTITIES_AVAILABLE = level_node['quantities'][0]['quantity'] if level_node['quantities'] else 0

                                        info = {
                                            "SKU": SKU,
                                            "TITLE": TITLE,
                                            "PRICE": PRICE,
                                            "PRICECOMPAREAT": PRICE_COMPARE_AT,
                                            "CATEGORY": CATEGORY,
                                            "SYNC_OP": "UPDATE",
                                            "SHOPIFY_PRODUCT_GID": PRODUCT_GID,
                                            "SHOPIFY_VARIANT_GID": VARIANT_GID,
                                            "SHOPIFY_INVENTORY_ITEM_GID": INVENTORY_ITEM_GID,
                                            "ID_LOCATION": LOCATION,
                                            "SHOPIFY_INVENTORY_LEVEL_GID": INVENTORY_LEVEL_GID,
                                            "QUANTITIES_AVAILABLE": QUANTITIES_AVAILABLE 
                                        }

                                        all_products.append(info)



                    print(f"Procesados {len(product_data)} productos. Total acumulado: {len(all_products)} registros")
                    
                    # Esperar 1 segundo antes de continuar (reducido de 4 segundos)
                    await asyncio.sleep(4)
                    
        except Exception as e:
            print(f"Error al procesar página: {e}")
            break

async def save_products_to_json():
    """Guardar todos los productos en un archivo JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"shopify_products_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"Productos guardados exitosamente en: {filename}")
        print(f"Total de registros guardados: {len(all_products)}")
    except Exception as e:
        print(f"Error al guardar archivo JSON: {e}")

async def main():
    """Función principal"""
    print("Iniciando extracción de productos de Shopify...")
    
    # Verificar que el token esté configurado
    if not headers['X-Shopify-Access-Token']:
        print("ERROR: Debes configurar el X-Shopify-Access-Token en el código")
        return
    
    try:
        await getInfo()
        await save_products_to_json()
        
        print("\n=== RESUMEN ===")
        print(f"Total de productos procesados: {len(all_products)}")
        print("Extracción completada exitosamente")
        
    except Exception as e:
        print(f"Error en la extracción: {e}")
        # Guardar lo que se haya obtenido hasta el momento
        if all_products:
            await save_products_to_json()

if __name__ == "__main__":
    asyncio.run(main())