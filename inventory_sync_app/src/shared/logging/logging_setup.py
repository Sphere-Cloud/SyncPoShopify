"""
Sistema de logging centralizado y estructurado
Ubicación: src/shared/logging/logging_setup.py
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from config.config_manager import get_config, LogLevel


class JSONFormatter(logging.Formatter):
    """
    Formatter personalizado para logs en formato JSON
    Útil para sistemas de monitoreo como ELK Stack
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Convierte el log record a formato JSON"""
        
        # Datos base del log
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Agregar campos personalizados si existen
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Campos específicos para tu aplicación
        if hasattr(record, 'sync_id'):
            log_data["sync_id"] = record.sync_id
        
        if hasattr(record, 'batch_id'):
            log_data["batch_id"] = record.batch_id
            
        if hasattr(record, 'sku'):
            log_data["sku"] = record.sku
            
        if hasattr(record, 'store_id'):
            log_data["store_id"] = record.store_id
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formatter con colores para la consola
    Mejora la legibilidad durante desarrollo
    """
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Aplica colores al mensaje de log"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Colorear solo el nivel del log
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


class InventorySyncLogger:
    """
    Clase principal para configurar el sistema de logging
    de tu aplicación de sincronización de inventario
    """
    
    def __init__(self):
        self.config = get_config()
        self._loggers_configured = set()
        self._setup_log_directory()
    
    def _setup_log_directory(self):
        """Crea el directorio de logs si no existe"""
        log_dir = Path(self.config.logging.log_dir)
        log_dir.mkdir(exist_ok=True)
    
    def setup_root_logger(self) -> logging.Logger:
        """
        Configura el logger raíz de la aplicación
        """
        root_logger = logging.getLogger()
        
        # Evitar configuración duplicada
        if root_logger.handlers:
            return root_logger
        
        root_logger.setLevel(self.config.logging.level.value)
        
        # Handler para archivo con rotación
        file_handler = self._create_file_handler()
        root_logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = self._create_console_handler()
        root_logger.addHandler(console_handler)
        
        # Handler para errores críticos (archivo separado)
        error_handler = self._create_error_handler()
        root_logger.addHandler(error_handler)
        
        return root_logger
    
    def _create_file_handler(self) -> logging.Handler:
        """Crea handler para archivo principal con rotación"""
        log_file = Path(self.config.logging.log_dir) / self.config.logging.log_filename
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,  # MB a bytes
            backupCount=self.config.logging.backup_count,
            encoding='utf-8'
        )
        
        if self.config.logging.json_format:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(self.config.logging.format))
        
        handler.setLevel(self.config.logging.level.value)
        return handler
    
    def _create_console_handler(self) -> logging.Handler:
        """Crea handler para salida por consola"""
        handler = logging.StreamHandler(sys.stdout)
        
        if self.config.environment.value == "development":
            # En desarrollo usar colores
            formatter = ColoredFormatter(self.config.logging.format)
        else:
            # En producción formato simple
            formatter = logging.Formatter(self.config.logging.format)
        
        handler.setFormatter(formatter)
        handler.setLevel(self.config.logging.level.value)
        return handler
    
    def _create_error_handler(self) -> logging.Handler:
        """Crea handler separado para errores críticos"""
        error_log = Path(self.config.logging.log_dir) / "errors.log"
        
        handler = logging.handlers.RotatingFileHandler(
            filename=error_log,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3,
            encoding='utf-8'
        )
        
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.ERROR)
        return handler
    
    def get_logger(self, name: str, level: Optional[LogLevel] = None) -> logging.Logger:
        """
        Obtiene un logger configurado para un componente específico
        
        Args:
            name: Nombre del logger (ej: 'erp.connector', 'shopify.updater')
            level: Nivel específico para este logger (opcional)
        """
        logger = logging.getLogger(name)
        
        # Configurar solo una vez
        if name not in self._loggers_configured:
            if level:
                logger.setLevel(level.value)
            
            # Configurar propagación
            logger.propagate = True
            
            self._loggers_configured.add(name)
        
        return logger
    
    def get_component_logger(self, component: str) -> logging.Logger:
        """
        Obtiene logger con configuración específica por componente
        
        Args:
            component: 'erp', 'shopify', 'database', 'sync'
        """
        logger_name = f"inventory_sync.{component}"
        
        # Niveles específicos por componente
        level_mapping = {
            'erp': self.config.logging.erp_log_level,
            'shopify': self.config.logging.shopify_log_level,
            'database': self.config.logging.database_log_level,
        }
        
        level = level_mapping.get(component, self.config.logging.level)
        return self.get_logger(logger_name, level)


# Instancia global del sistema de logging
_logging_system = None


def setup_logging() -> InventorySyncLogger:
    """
    Función principal para inicializar el sistema de logging
    Llamar al inicio de la aplicación
    """
    global _logging_system
    
    if _logging_system is None:
        _logging_system = InventorySyncLogger()
        _logging_system.setup_root_logger()
        
        # Log inicial de la aplicación
        logger = _logging_system.get_logger("app.startup")
        config = get_config()
        logger.info(
            f"Iniciando {config.app_name} v{config.app_version} "
            f"en ambiente {config.environment.value}"
        )
    
    return _logging_system


def get_logger(name: str) -> logging.Logger:
    """
    Función helper para obtener un logger
    
    Usage:
        from shared.logging import get_logger
        logger = get_logger('erp.connector')
    """
    if _logging_system is None:
        setup_logging()
    
    return _logging_system.get_logger(name)


def get_component_logger(component: str) -> logging.Logger:
    """
    Función helper para obtener logger de componente
    
    Usage:
        from shared.logging import get_component_logger
        logger = get_component_logger('erp')
    """
    if _logging_system is None:
        setup_logging()
    
    return _logging_system.get_component_logger(component)


class LoggerMixin:
    """
    Mixin para agregar logging a cualquier clase
    
    Usage:
        class ERPConnector(LoggerMixin):
            def __init__(self):
                super().__init__()
                self.logger.info("ERP Connector inicializado")
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Context manager para logging de operaciones
class LogOperation:
    """
    Context manager para loggear operaciones completas
    
    Usage:
        with LogOperation("sync_inventory", logger, sync_id="12345"):
            # tu código aquí
            pass
    """
    
    def __init__(self, operation: str, logger: logging.Logger, **extra_fields):
        self.operation = operation
        self.logger = logger
        self.extra_fields = extra_fields
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(
            f"Iniciando operación: {self.operation}",
            extra={'extra_fields': self.extra_fields}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Operación completada: {self.operation} "
                f"(duración: {duration.total_seconds():.2f}s)",
                extra={'extra_fields': {**self.extra_fields, 'duration_seconds': duration.total_seconds()}}
            )
        else:
            self.logger.error(
                f"Operación falló: {self.operation} "
                f"(duración: {duration.total_seconds():.2f}s) "
                f"Error: {exc_val}",
                extra={'extra_fields': {**self.extra_fields, 'duration_seconds': duration.total_seconds()}},
                exc_info=True
            )
        
        return False  # No suprimir excepciones