# ===================================================
# src/shared/__init__.py
# ===================================================
"""
Módulo de utilidades compartidas
Contiene configuración, logging y excepciones
"""

from .config.config_manager import get_config, ApplicationConfig
from .logging.logging_setup import setup_logging, get_logger, get_component_logger

__all__ = [
    "get_config",
    "ApplicationConfig", 
    "setup_logging",
    "get_logger",
    "get_component_logger"
]