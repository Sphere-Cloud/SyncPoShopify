#!/usr/bin/env python3
import sys
import os
import asyncio

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.main import main
from src.shared.config.config_manager import get_config, print_config_status

if __name__ == "__main__":
    config = get_config()

    #print_config_status()

    asyncio.run(main(config=config))