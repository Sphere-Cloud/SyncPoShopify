from domain.repositories.IERPDataExtractor import IERPDataExtractor

from domain.entities.KordataProduct import KordataProduct

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

import aiohttp
import asyncio

class ERPDataExtractor(IERPDataExtractor):
    """IMPLEMENTACIÓN CONCRETA: Extrae datos de tu endpoint ERP"""
    
    def __init__(self, endpoint_url: str, bearer_token: str, timeout: int = 20000):
        self._endpoint_url = endpoint_url
        self._timeout = timeout
        self._last_extraction_time = 0.0
        self._bearer_token = bearer_token

    # 1. PROBLEMA: int('') falla
    # SOLUCIÓN: Función helper para conversión segura
    def safe_int(self, value):
        """Convierte de manera segura un valor a int"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def safe_float(self, value):
        """Convierte de manera segura un valor a float"""
        if value is None or value == '' or value == 'None':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def safe_str(self, value):
        """Convierte de manera segura un valor a string"""
        if value is None or value == 'None':
            return ''
        return str(value).strip()
    
    async def extract_products(self) -> List[KordataProduct]:
        """Implementación real: llama a tu endpoint ERP"""
        start_time = datetime.now()

        payload = { "query": "query reporteInventarios { BasesReportesGenerarReportePorId(data: {id: 1144} valoresParametros: [{clave: \"productoId\", valor: \"null\"}, {clave: \"modelo\", valor: \"null\"}, {clave: \"categoriaId\", valor: \"null\"}, {clave: \"almacenId\", valor: \"null\"}, {clave: \"proveedorId\", valor: \"null\"}, {clave: \"marcaId\", valor: \"null\"}, {clave: \"tipoProductoId\", valor: \"null\"}, {clave: \"existenciaMenorCero\", valor: \"false\"}, {clave: \"existenciaMayorCero\", valor: \"false\"}]) { resultadoReporteHashmap } }" }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {self._bearer_token}"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self._timeout)) as session:
            async with session.post(self._endpoint_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"ERP endpoint failed: {response.status} - {response.reason}")
                
                data = await response.json()
                
                products = data['data']['BasesReportesGenerarReportePorId']['resultadoReporteHashmap']
                # Convertir JSON del ERP a entidades de dominio
                erp_products = []
                
                for index, item in enumerate(products):  # Tu JSON tiene esta estructura

                    # new_existencia = float(item["Existencia"])

                    if index >= 1:

                        print(item)

                        try:
                            erp_product = KordataProduct(
                                    id=self.safe_int(item.get('id')),
                                    sku=item.get('SKU'),
                                    modelo=self.safe_str(item.get('Modelo')),
                                    talla=self.safe_str(item.get('Talla')),
                                    color=self.safe_str(item.get('Color')),
                                    nombre=self.safe_str(item.get('Nombre')),
                                    categoria=self.safe_str(item.get('Categoría')),
                                    proveedor=self.safe_str(item.get('Proveedor')),
                                    marca=self.safe_str(item.get('Marca')),
                                    almacen=self.safe_str(item.get('Almacén')),
                                    costo=self.safe_float(item.get('Costo')),
                                    precio_venta=self.safe_float(item.get('Precio venta')),
                                    existencia=self.safe_float(item.get('Existencia')),
                                    reservado=self.safe_float(item.get('Reservado')),
                                    disponible=self.safe_float(item.get('Disponible'))
                                )
                        
                            # Solo agregar productos válidos (regla de negocio)
                            erp_products.append(erp_product)

                        except Exception as e:
                            print(f"Error creando KordataProduct: {e}")
                            print(f"Item problemático: {item}")
                            continue  # o manejar según tu lógica
                
                self._last_extraction_time = (datetime.now() - start_time).total_seconds()
                return erp_products
    
    async def get_extraction_metadata(self) -> Dict[str, Any]:
        return {
            "last_extraction_time": self._last_extraction_time,
            "endpoint": self._endpoint_url
        }