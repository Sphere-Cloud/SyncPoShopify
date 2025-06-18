#!/usr/bin/env python

import psycopg2 as pg
import json



# PostgreSQL Data Connection
DB_HOST = "localhost"
DB_PORT = "5232"
DB_NAME = "POS_SYNC_SHOPI"
DB_USER = "postgres"
DB_PASSWORD = "12345"
TABLE_NAME = "<table-name>"

# Read the JSON data from the file
with open('./filtered_data/data.json', encoding='utf-8') as f:
    data = json.load(f)


#Connect to PostgreSQL
conn = pg.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

for product in data:
    pos_sku = product['Codigo']
    title = product['Descripcion']
    description = ""
    category = ""
    status = ""
    shopify_product_gid = ""
    shopify_variant_gid = ""
    inventory_item_gid = ""
    created_at = ""
    updated_at = ""

    location_name = "default"
    quantities_available = product['Existencia']
    shopify_invengory_level_gid = ""
    


conn.commit()
conn.close()