#!/usr/bin/env python3
import sys
import os
import asyncio

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.main import main

if __name__ == "__main__":
    asyncio.run(main())