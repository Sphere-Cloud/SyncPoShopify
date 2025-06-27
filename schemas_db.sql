-- Tabla principal de productos Shopify
CREATE TABLE "shopify_product" (
  "pos_sku" VARCHAR(30) PRIMARY KEY,
  "title" VARCHAR(100) NOT NULL,
  "description" TEXT,
  "price" FLOAT,
  "price_compare" FLOAT,
  "category" VARCHAR(50),
  "sync_op" VARCHAR(20) DEFAULT 'CREATE',
  "shopify_product_gid" VARCHAR(100) UNIQUE,
  "shopify_variant_gid" VARCHAR(100) UNIQUE,
  "shopify_inventory_item_gid" VARCHAR(100) UNIQUE,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ubicaciones Shopify
CREATE TABLE "shopify_location" (
  "id_location" SERIAL PRIMARY KEY,
  "name" VARCHAR(100) NOT NULL,
  "shopify_location_gid" VARCHAR(100) UNIQUE
);

-- Tabla de log de sincronización de productos
CREATE TABLE "product_sync_log" (
  "sync_id" SERIAL PRIMARY KEY,
  "pos_sku" VARCHAR(30) NOT NULL,
  "sync_info" TEXT,
  "before_sync" INTEGER CHECK (before_sync >= 0),
  "after_sync" INTEGER CHECK (after_sync >= 0),
  "synced_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "synced_status" VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  "sync_type" VARCHAR(20) NOT NULL,
  CONSTRAINT "fk_product_sync_log_pos_sku"
    FOREIGN KEY ("pos_sku")
    REFERENCES "shopify_product"("pos_sku")
    ON DELETE CASCADE
);

-- Tabla de niveles de inventario Shopify (ACTUALIZADA)
CREATE TABLE "shopify_inventory_level" (
  "inventory_level_id" SERIAL PRIMARY KEY,
  "pos_sku" VARCHAR(30) NOT NULL,
  "id_location" INTEGER NOT NULL,
  "shopify_inventory_level_gid" VARCHAR(100) UNIQUE,
  "quantities_available" FLOAT NOT NULL DEFAULT 0 CHECK (quantities_available >= 0),
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "fk_shopify_inventory_level_pos_sku"
    FOREIGN KEY ("pos_sku")
    REFERENCES "shopify_product"("pos_sku")
    ON DELETE CASCADE,
  CONSTRAINT "fk_shopify_inventory_level_location"
    FOREIGN KEY ("id_location")
    REFERENCES "shopify_location"("id_location")
    ON DELETE CASCADE,
  CONSTRAINT "uq_inventory_level_sku_location"
    UNIQUE ("pos_sku", "id_location")
);

-- Índices para mejorar el rendimiento
CREATE INDEX "idx_shopify_product_gid" ON "shopify_product"("shopify_product_gid");
CREATE INDEX "idx_shopify_variant_gid" ON "shopify_product"("shopify_variant_gid");
CREATE INDEX "idx_inventory_item_gid" ON "shopify_product"("shopify_inventory_item_gid");
CREATE INDEX "idx_shopify_location_gid" ON "shopify_location"("shopify_location_gid");
CREATE INDEX "idx_inventory_level_pos_sku" ON "shopify_inventory_level"("pos_sku");
CREATE INDEX "idx_inventory_level_location" ON "shopify_inventory_level"("id_location");

-- Función para actualizar el timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar automáticamente updated_at
CREATE TRIGGER update_shopify_product_updated_at 
    BEFORE UPDATE ON "shopify_product"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopify_inventory_level_updated_at 
    BEFORE UPDATE ON "shopify_inventory_level"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


