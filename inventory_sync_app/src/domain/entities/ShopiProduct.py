from dataclasses import dataclass

@dataclass
class ShopiProduct:
    """
    Entidad para representar la informacion que se guarda en db 
    cuando un producto nuevo es agregado a shopify, y sus variantes
    """
    pos_sku: str
    id_location: int
    new_quantity: int = 0
    shopify_product_gid: str=""
    shopify_variant_gid: str=""
    shopify_inventory_item_gid: str=""
    shopify_inventory_level_gid: str=""


    
