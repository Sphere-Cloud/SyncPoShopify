CREATE TABLE "shopify_product" (
  "pos_sku" VARCHAR(30) PRIMARY KEY,
  "title" VARCHAR(100),
  "description" VARCHAR(500),
  "category" VARCHAR(50),
  "status" VARCHAR(20),
  "shopify_product_gid" VARCHAR(100),
  "shopify_variant_gid" VARCHAR(100),
  "inventory_item_gid" VARCHAR(100),
  "created_at" TIMESTAMP NOT NULL DEFAULT(NOW()),
  "updated_at" TIMESTAMP NOT NULL DEFAULT(NOW())
);

CREATE TABLE "product_sync_log" (
  "sync_id" SERIAL PRIMARY KEY,
  "sku_pos" VARCHAR(30),
  "sync_info" VARCHAR(500),
  "before_sync" INTEGER,
  "after_sync" INTEGER,
  "synced_at" TIMESTAMP NOT NULL DEFAULT(NOW()),
  "synced_status" VARCHAR(20),
  "sync_type" VARCHAR(20),
  CONSTRAINT "FK_product_sync_log_sku_pos"
    FOREIGN KEY ("sku_pos")
    REFERENCES "shopify_product"("pos_sku")
);

CREATE TABLE "shopify_inventory_level" (
  "inventory_level_id" SERIAL PRIMARY KEY,
  "pos_sku" VARCHAR(30),
  "shopify_inventory_level_gid" VARCHAR(100),
  "location_name" VARCHAR(100),
  "quantities_available" INTEGER,
  "updated_at" TIMESTAMP NOT NULL DEFAULT(NOW()),
  CONSTRAINT "FK_shopify_inventory_level_pos_sku"
    FOREIGN KEY ("pos_sku")
    REFERENCES "shopify_product"("pos_sku")
);
