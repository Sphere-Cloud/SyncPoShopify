import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
import aiohttp
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar las clases necesarias
from src.infrastructure.ShopifyInventoryUpdater import ShopifyInventoryUpdater
from src.domain.entities.InventoryChange import InventoryChange
from src.domain.entities.ProductSyncLog import ProductSyncLog


class TestShopifyInventoryUpdater:
    
    @pytest.fixture
    def shopify_updater(self):
        """Fixture para crear una instancia del updater"""
        # return ShopifyInventoryUpdater(
            
        # )

        pass
    
    @pytest.fixture
    def sample_inventory_change(self):
        """Fixture para crear un cambio de inventario de prueba"""
        return InventoryChange(
            sku="TEST-SKU-001",
            old_quantity=50,
            new_quantity=45,
            sync_op="UPDATE",
            shopify_inventory_item="gid://shopify/InventoryItem/49046106505373",
            id_location="gid://shopify/Location/76147490973",
            title="Test Product"
        )
    
    @pytest.fixture
    def sample_create_change(self):
        """Fixture para crear un cambio de creación de producto"""
        return InventoryChange(
            sku="NEW-SKU-001",
            old_quantity=0,
            new_quantity=15,
            sync_op="CREATE",
            shopify_inventory_item=None,
            id_location="gid://shopify/Location/76147490973",
            title="New Test Product"
        )


class TestUpdateInventory:
    """Tests para actualización de inventario"""
    
    @pytest.mark.asyncio
    async def test_update_inventory_success(self, shopify_updater, update_change):
        """Test de actualización exitosa de inventario"""
        # Mock de respuesta exitosa de Shopify
        success_response = {
            "data": {
                "inventorySetQuantities": {
                "inventoryAdjustmentGroup": {
                    "createdAt": None,
                    "reason": "movement_updated",
                    "referenceDocumentUri": None,
                    "changes": [
                    {
                        "name": "available",
                        "delta": 5
                    },
                    {
                        "name": "on_hand",
                        "delta": 5
                    }
                    ]
                },
                "userErrors": []
                }
            },
            "extensions": {
                "cost": {
                "requestedQueryCost": 11,
                "actualQueryCost": 11,
                "throttleStatus": {
                    "maximumAvailable": 2000,
                    "currentlyAvailable": 1989,
                    "restoreRate": 100
                }
                }
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Configurar mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=success_response)
            
            # Configurar session mock
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Ejecutar test
            result = await shopify_updater._update_single_inventory(update_change)
            
            # Verificar resultado
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_batch_success(self, shopify_updater, update_change):
        """Test de actualización en lote exitosa"""
        with patch.object(shopify_updater, '_update_single_inventory', return_value=True):
            result = await shopify_updater.update_inventory_batch([update_change])
            
            # Verificar que se procesó correctamente
            assert len(result) == 1
            assert result[0].sku_pos == "TEST-SKU-UPDATE"
            assert result[0].synced_status == "SUCCESS"
            assert result[0].sync_type == "UPDATE"
            assert result[0].before_sync == 10
            assert result[0].after_sync == 25


class TestCreateInventory:
    """Tests para creación de productos"""
    
    @pytest.mark.asyncio
    async def test_create_inventory_success(self, shopify_updater, create_change):
        """Test de creación exitosa de producto"""
        # Mock responses para cada paso del proceso de creación
        create_product_response = {
            "data": {
                "productCreate": {
                    "product": {
                        "id": "gid://shopify/Product/123",
                        "variants": {
                            "edges": [{
                                "node": {
                                    "id": "gid://shopify/ProductVariant/456",
                                    "inventoryItem": {
                                        "id": "gid://shopify/InventoryItem/789"
                                    }
                                }
                            }]
                        }
                    }
                }
            }
        }
        
        # Respuestas para los otros pasos (tracking, activate, set quantity)
        generic_success_response = {
            "data": {
                "productVariantsBulkUpdate": {"userErrors": []},
                "inventoryActivate": {
                    "inventoryLevel": {"id": "gid://shopify/InventoryLevel/999"}
                },
                "inventorySetQuantities": {"userErrors": []}
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Simular las 4 respuestas del proceso de creación
            mock_response.json = AsyncMock(side_effect=[
                create_product_response,    # 1. Crear producto
                generic_success_response,   # 2. Habilitar tracking
                generic_success_response,   # 3. Activar inventario
                generic_success_response    # 4. Establecer cantidad
            ])
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Ejecutar test
            result = await shopify_updater._create_single_inventory(create_change)
            
            # Verificar resultado
            assert result is True
    
    @pytest.mark.asyncio
    async def test_create_batch_success(self, shopify_updater, create_change):
        """Test de creación en lote exitosa"""
        with patch.object(shopify_updater, '_create_single_inventory', return_value=True):
            result = await shopify_updater.update_inventory_batch([create_change])
            
            # Verificar que se procesó correctamente
            assert len(result) == 1
            assert result[0].sku_pos == "TEST-SKU-CREATE"
            assert result[0].synced_status == "SUCCESS"
            assert result[0].sync_type == "CREATE"
            assert result[0].before_sync == 0
            assert result[0].after_sync == 15

class TestMixedOperations:
    """Tests para operaciones mixtas"""
    
    @pytest.mark.asyncio
    async def test_mixed_batch_success(self, shopify_updater, update_change, create_change):
        """Test de lote mixto (crear y actualizar) exitoso"""
        changes = [update_change, create_change]
        
        with patch.object(shopify_updater, '_update_single_inventory', return_value=True):
            with patch.object(shopify_updater, '_create_single_inventory', return_value=True):
                result = await shopify_updater.update_inventory_batch(changes)
                
                # Verificar que se procesaron ambos correctamente
                assert len(result) == 2
                
                # Verificar UPDATE
                assert result[0].sync_type == "UPDATE"
                assert result[0].synced_status == "SUCCESS"
                
                # Verificar CREATE
                assert result[1].sync_type == "CREATE"
                assert result[1].synced_status == "SUCCESS"

# Configuración para usar las fixtures
TestUpdateInventory = type('TestUpdateInventory', (TestUpdateInventory, TestShopifyInventoryUpdater), {})
TestCreateInventory = type('TestCreateInventory', (TestCreateInventory, TestShopifyInventoryUpdater), {})
# TestMixedOperations = type('TestMixedOperations', (TestMixedOperations, TestShopifyInventoryUpdater), {})


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])