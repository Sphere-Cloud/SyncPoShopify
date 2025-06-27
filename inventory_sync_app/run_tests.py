#!/usr/bin/env python3
"""
Script simple para ejecutar tests del ShopifyInventoryUpdater
"""

import subprocess
import sys
import os

def run_tests():
    """Ejecuta los tests básicos"""
    print("🧪 Ejecutando tests de ShopifyInventoryUpdater...")
    print("="*50)
    
    # Cambiar al directorio del proyecto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    try:
        # Ejecutar tests con pytest desde el directorio del proyecto
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/test_shopify_inventory_updater.py", 
            "-v",
            "--tb=short"
        ], check=True, cwd=project_dir)
        
        print("\n✅ Todos los tests pasaron exitosamente!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Algunos tests fallaron (código: {e.returncode})")
        return 1
    except FileNotFoundError:
        print("❌ pytest no está instalado. Ejecuta: pip install pytest pytest-asyncio")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())