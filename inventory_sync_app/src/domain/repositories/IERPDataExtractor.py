from domain.entities.KordataProduct import KordataProduct

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class IERPDataExtractor(ABC):
    """Contrato para extraer datos del ERP"""
    @abstractmethod
    async def extract_products(self) -> List[KordataProduct]:
        pass
    
    @abstractmethod
    async def get_extraction_metadata(self) -> Dict[str, Any]:
        pass