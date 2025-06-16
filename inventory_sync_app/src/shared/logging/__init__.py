# ===================================================
# src/shared/logging/__init__.py
# ===================================================
"""
Sistema de logging centralizado y estructurado
"""

from .logging_setup import (
    setup_logging,
    get_logger,
    get_component_logger,
    LoggerMixin,
    LogOperation,
    InventorySyncLogger,
    JSONFormatter,
    ColoredFormatter
)

__all__ = [
    "setup_logging",
    "get_logger", 
    "get_component_logger",
    "LoggerMixin",
    "LogOperation",
    "InventorySyncLogger",
    "JSONFormatter",
    "ColoredFormatter"
]