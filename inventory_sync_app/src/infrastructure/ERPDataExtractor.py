from domain.repositories.IERPDataExtractor import IERPDataExtractor

from domain.entities.ERPProduct import ERPProduct

from typing import List, Optional, Dict, Any
from datetime import datetime

class ERPDataExtractor(IERPDataExtractor):
    """IMPLEMENTACIÓN CONCRETA: Extrae datos de tu endpoint ERP"""
    
    def __init__(self, endpoint_url: str, timeout: int = 15):
        self._endpoint_url = endpoint_url
        self._timeout = timeout
        self._last_extraction_time = 0.0
    
    async def extract_products(self) -> List[ERPProduct]:
        """Implementación real: llama a tu endpoint ERP"""
        start_time = datetime.now()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
            async with session.get(self._endpoint_url) as response:
                if response.status != 200:
                    raise Exception(f"ERP endpoint failed: {response.status}")
                
                data = await response.json()
                
                # Convertir JSON del ERP a entidades de dominio
                erp_products = []
                for item in data:  # Tu JSON tiene esta estructura
                    erp_product = ERPProduct(
                        codigo=item["Codigo"],
                        descripcion=item["Descripcion"],
                        unidad=item["Unidad"],
                        precio=Decimal(str(item["Precio"])),
                        precio_con_imp=Decimal(str(item["PrecioConImp"])),
                        existencia=int(item["Existencia"]),
                        grupo2=item.get("Grupo2"),
                        desc_grupo2=item.get("DescGrupo2"),
                        agrupacion2=item.get("Agrupacion2"),
                        desc_agrup2=item.get("DescAgrup2"),
                        imagen_bit=item.get("ImagenBit", "")
                    )
                    
                    # Solo agregar productos válidos (regla de negocio)
                    if erp_product.is_valid_for_sync():
                        erp_products.append(erp_product)
                
                self._last_extraction_time = (datetime.now() - start_time).total_seconds()
                return erp_products
    
    async def get_extraction_metadata(self) -> Dict[str, Any]:
        return {
            "last_extraction_time": self._last_extraction_time,
            "endpoint": self._endpoint_url
        }