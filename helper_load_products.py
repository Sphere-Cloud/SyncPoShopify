#!/usr/bin/env python3

import psycopg2 as pg
from psycopg2.extras import execute_batch
import json
import os
import logging
from typing import List, Dict, Any
from contextlib import contextmanager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),  # Puerto estándar de PostgreSQL
    "dbname": os.getenv("DB_NAME", ""),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "12345")
}

# Constantes
DATA_FILE_PATH = './shopify_products_20250704_230818.json'
DEFAULT_LOCATIONS = ["default"]
BATCH_SIZE = 1000


@contextmanager
def get_db_connection():
    """Context manager para manejo seguro de conexiones a la base de datos"""
    conn = None
    try:
        conn = pg.connect(**DB_CONFIG)
        yield conn
    except pg.Error as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """Carga y valida los datos del archivo JSON"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("El archivo JSON debe contener una lista de productos")
        
        logger.info(f"Cargados {len(data)} productos del archivo JSON")
        return data
    
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        logger.error(f"Error al cargar datos JSON: {e}")
        raise


def validate_product_data(product: Dict[str, Any]) -> bool:
    """Valida que el producto tenga los campos requeridos y que ninguno esté vacío"""
    required_fields = [
        "SKU", 
        "TITLE", 
        "PRICE", 
        "PRICECOMPAREAT", 
        "CATEGORY", 
        "SYNC_OP", 
        "SHOPIFY_PRODUCT_GID", 
        "SHOPIFY_VARIANT_GID", 
        "SHOPIFY_INVENTORY_ITEM_GID", 
        "ID_LOCATION",
        "SHOPIFY_INVENTORY_LEVEL_GID",
        "QUANTITIES_AVAILABLE"
    ]
    
    for field in required_fields:
        # Verificar que el campo existe
        if field not in product:
            logger.warning(f"Producto omitido: falta el campo '{field}'")
            return False
        
        # Verificar que el campo no esté vacío según su tipo
        value = product[field]
        
        # Para campos de texto (strings)
        if field in ['SKU', 'TITLE', 'SYNC_OP', 'SHOPIFY_PRODUCT_GID', 
                    'SHOPIFY_VARIANT_GID', 'SHOPIFY_INVENTORY_ITEM_GID', 'SHOPIFY_INVENTORY_LEVEL_GID']:
            if not value or (isinstance(value, str) and value.strip() == ""):
                logger.warning(f"Producto omitido: el campo '{field}' está vacío")
                return False
        
        # Para campos numéricos
        elif field in ['PRICE', 'PRICECOMPAREAT', 'ID_LOCATION', 'QUANTITIES_AVAILABLE']:
            if value is None:
                logger.warning(f"Producto omitido: el campo '{field}' es None")
                return False
            # Permitir 0 como valor válido para números
            try:
                float(value)  # Verificar que sea convertible a número
            except (ValueError, TypeError):
                logger.warning(f"Producto omitido: el campo '{field}' no es un número válido: {value}")
                return False
    
    return True

def debug_product_fields(product: Dict[str, Any]) -> None:
    """Función para debuggear qué campos existen realmente"""
    print("Campos disponibles en el producto:")
    for key, value in product.items():
        print(f"  '{key}': {type(value).__name__} = {value}")
    print()



def prepare_product_data(product: Dict[str, Any]) -> tuple:
    """Prepara los datos del producto para inserción"""
    return (
            product.get('SKU', ''),
            product.get('TITLE', ''),
            product.get('PRICE', 0.0),
            product.get('PRICECOMPAREAT', 0.0),
            product.get('CATEGORY', ''),
            product.get('SYNC_OP', 'UPDATE'),
            product.get('SHOPIFY_PRODUCT_GID', ''),
            product.get('SHOPIFY_VARIANT_GID', ''),
            product.get('SHOPIFY_INVENTORY_ITEM_GID', ''),
        )


def prepare_inventory_data(product: Dict[str, Any]) -> List[tuple]:
    """Prepara los datos de inventario para inserción"""
    SKU = product['SKU']
    QUANTITIES_AVAILABLE = product['QUANTITIES_AVAILABLE']
    LOCATION = product['ID_LOCATION']
    SHOPIFY_INVENTORY_LEVEL_GID = product['SHOPIFY_INVENTORY_LEVEL_GID']
    
    return [
        (
            SKU,                               # pos_sku                               # shopify_inventory_level_gid
            LOCATION,                          # location_name
            QUANTITIES_AVAILABLE,              # quantities_available
            SHOPIFY_INVENTORY_LEVEL_GID
        )
    ]

def insert_location_batch(cursor) -> None:
    locations = [ 
        ( "CEDIS/Envio Nacional","gid://shopify/Location/36497621067" ), 
        ( "PT Coacalco", "gid://shopify/Location/102034047266" ), 
        ( "PT Puebla", "gid://shopify/Location/33331740747" ), 
        ( "PT Querétaro", "gid://shopify/Location/95186059554" ), 
        ( "PT Reyes/La Paz", "gid://shopify/Location/104483127586" ), 
        ( "PT Tijuana", "gid://shopify/Location/60907257931" ), 
        ( "PT Toluca", "gid://shopify/Location/105435693346" ), 
        ( "PT Toreo/Pericentro", "gid://shopify/Location/60914368587" ),
        ( "Eje Central", "gid://shopify/Location/107999363362")
    ]
    """Inserta locations en lotes para mejor rendimiento"""
    insert_query = """
        INSERT INTO shopify_location
        (name,shopify_location_gid)
        VALUES (%s, %s)
    """
    
    execute_batch(cursor, insert_query, locations, page_size=BATCH_SIZE)
    logger.info(f"Insertados/actualizados {len(locations)} Locaciones")

def insert_products_batch(cursor, products_data: List[tuple]) -> None:
    """Inserta productos en lotes para mejor rendimiento"""
    insert_query = """
        INSERT INTO shopify_product 
        (pos_sku, title, price, price_compare, category, sync_op, shopify_product_gid, shopify_variant_gid, shopify_inventory_item_gid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (pos_sku) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            updated_at = CURRENT_TIMESTAMP
    """
    
    execute_batch(cursor, insert_query, products_data, page_size=BATCH_SIZE)
    logger.info(f"Insertados/actualizados {len(products_data)} productos")


def insert_inventory_batch(cursor, inventory_data: List[tuple]) -> None:
    """Inserta datos de inventario en lotes"""
    insert_query = """
        INSERT INTO shopify_inventory_level 
        (pos_sku, id_location, quantities_available, shopify_inventory_level_gid)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (pos_sku, id_location) DO UPDATE SET
            quantities_available = EXCLUDED.quantities_available,
            updated_at = CURRENT_TIMESTAMP
    """
    
    execute_batch(cursor, insert_query, inventory_data, page_size=BATCH_SIZE)
    logger.info(f"Insertados/actualizados {len(inventory_data)} registros de inventario")


def main():
    """Función principal del script"""
    try:
        # Cargar datos
        logger.info("Iniciando importación de datos...")
        data = load_json_data(DATA_FILE_PATH)
        #print(data)
        
        # Validar y preparar datos
        valid_products = [product for product in data if validate_product_data(product)]
        logger.info(f"Productos válidos: {len(valid_products)} de {len(data)}")
        
        #valid_products = []

        if not valid_products:
            logger.error("No hay productos válidos para importar")
            return
        
        # Preparar datos para inserción
        products_data = [prepare_product_data(product) for product in valid_products]
        
        inventory_data = []
        for product in valid_products:
            inventory_data.extend(prepare_inventory_data(product))

        #print(inventory_data)
        
        # Insertar datos en la base de datos
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                # Insertar Locaciones
                #insert_location_batch(cursor)
                #conn.commit()
                #logger.info("Locaciones Cargadas")

                # Insertar productos
                insert_products_batch(cursor, products_data)
                conn.commit()
                logger.info("Productos Cargados")
                
                # Insertar inventario
                insert_inventory_batch(cursor, inventory_data)
                conn.commit()
                logger.info("Inventarios Cargados")
                
                #Confirmar transacción
                conn.commit()
                logger.info("Importación completada exitosamente")
                pass
    
    except Exception as e:
        logger.error(f"Error durante la importación: {e}")
        raise


if __name__ == "__main__":
    main()