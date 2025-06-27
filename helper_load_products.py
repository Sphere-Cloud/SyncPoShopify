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
    "dbname": os.getenv("DB_NAME", "POS_SYNC_SHOPI"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "12345")
}

# Constantes
DATA_FILE_PATH = './data_examples/filtered_data.json'
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
    """Valida que el producto tenga los campos requeridos"""
    required_fields = ['Codigo', 'Descripcion']
    
    for field in required_fields:
        if field not in product or not product[field]:
            logger.warning(f"Producto omitido: falta el campo '{field}' o está vacío")
            return False
    
    # Validar que Existencia sea un número
    try:
        float(product.get('Existencia', 0))
    except (ValueError, TypeError):
        logger.warning(f"Producto {product.get('Codigo', 'UNKNOWN')} omitido: 'Existencia' no es un número válido")
        return False
    
    return True


def prepare_product_data(product: Dict[str, Any]) -> tuple:
    """Prepara los datos del producto para inserción"""
    return (
        product['Codigo'],                    # pos_sku
        product['Descripcion'][:100],         # title (truncado)
        product.get('Descripcion_Larga', ''), # description
        product.get('Categoria', ''),          # category
        product['Precio'],
        product.get('Precio Compare', 0.0)
    )


def prepare_inventory_data(product: Dict[str, Any], locations: List[str]) -> List[tuple]:
    """Prepara los datos de inventario para inserción"""
    pos_sku = product['Codigo']
    quantities_available = float(product.get('Existencia', 0))
    
    return [
        (
            pos_sku,                          # pos_sku                               # shopify_inventory_level_gid
            location,                         # location_name
            quantities_available              # quantities_available
        )
        for location in locations
    ]

def insert_location_batch(cursor) -> None:
    locations = [("CEDIS","gid://shopify/Location/76147490973")]
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
        (pos_sku, title, description, category, price, price_compare)
        VALUES (%s, %s, %s, %s, %s, %s)
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
        (pos_sku, id_location, quantities_available)
        VALUES (%s, %s, %s)
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
        
        # Validar y preparar datos
        valid_products = [product for product in data if validate_product_data(product)]
        logger.info(f"Productos válidos: {len(valid_products)} de {len(data)}")
        
        if not valid_products:
            logger.error("No hay productos válidos para importar")
            return
        
        # Preparar datos para inserción
        products_data = [prepare_product_data(product) for product in valid_products]
        
        inventory_data = []
        for product in valid_products:
            inventory_data.extend(prepare_inventory_data(product, [1]))
        
        # Insertar datos en la base de datos
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                # Insertar Locaciones
                insert_location_batch(cursor)
                conn.commit()
                logger.info("Locaciones Cargadas")

                # Insertar productos
                insert_products_batch(cursor, products_data)
                conn.commit()
                logger.info("Productos Cargados")
                
                # Insertar inventario
                insert_inventory_batch(cursor, inventory_data)
                conn.commit()
                logger.info("Inventarios Cargados")
                
                # Confirmar transacción
                conn.commit()
                logger.info("Importación completada exitosamente")
    
    except Exception as e:
        logger.error(f"Error durante la importación: {e}")
        raise


if __name__ == "__main__":
    main()