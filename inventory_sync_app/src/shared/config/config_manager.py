"""
Sistema de configuración centralizado usando Pydantic
Ubicación: src/shared/config/config_manager.py
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator, Field
from enum import Enum


class Environment(str, Enum):
    """Ambientes disponibles"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveles de logging disponibles"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Configuración de base de datos"""
    host: str = Field(..., env="DB_HOST")
    port: int = Field(5432, env="DB_PORT")
    name: str = Field(..., env="DB_NAME")
    user: str = Field(..., env="DB_USER")
    password: str = Field(..., env="DB_PASSWORD")
    pool_size: int = Field(10, env="DB_POOL_SIZE")
    max_overflow: int = Field(20, env="DB_MAX_OVERFLOW")
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a la base de datos"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Configuración de Redis/Cache"""
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    db: int = Field(0, env="REDIS_DB")
    max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    
    # TTL específicos para tu aplicación
    erp_data_ttl: int = Field(12, env="ERP_DATA_TTL_SECONDS")  # 12 segundos como mencionaste
    inventory_cache_ttl: int = Field(3600, env="INVENTORY_CACHE_TTL")  # 1 hora


class ERPConfig(BaseSettings):
    """Configuración del ERP"""
    endpoint_url: str = Field(..., env="ERP_ENDPOINT_URL")
    api_key: Optional[str] = Field(None, env="ERP_API_KEY")
    username: Optional[str] = Field(None, env="ERP_USERNAME")
    password: Optional[str] = Field(None, env="ERP_PASSWORD")
    timeout_seconds: int = Field(15, env="ERP_TIMEOUT_SECONDS")  # 15 seg (3 más que los 12 típicos)
    max_retries: int = Field(3, env="ERP_MAX_RETRIES")
    retry_delay: int = Field(5, env="ERP_RETRY_DELAY_SECONDS")


class ShopifyConfig(BaseSettings):
    """Configuración de Shopify"""
    api_key: str = Field(..., env="SHOPIFY_API_KEY")
    api_secret: str = Field(..., env="SHOPIFY_API_SECRET")
    access_token: str = Field(..., env="SHOPIFY_ACCESS_TOKEN")
    shop_domain: str = Field(..., env="SHOPIFY_SHOP_DOMAIN")  # tu-tienda.myshopify.com
    api_version: str = Field("2024-01", env="SHOPIFY_API_VERSION")
    
    # Rate limiting settings
    max_requests_per_second: int = Field(35, env="SHOPIFY_MAX_RPS")  # 35 de 40 para margen
    max_burst_requests: int = Field(80, env="SHOPIFY_MAX_BURST")
    backoff_factor: float = Field(1.5, env="SHOPIFY_BACKOFF_FACTOR")
    max_backoff_seconds: int = Field(300, env="SHOPIFY_MAX_BACKOFF")  # 5 minutos máximo


class SyncConfig(BaseSettings):
    """Configuración específica del proceso de sincronización"""
    batch_size: int = Field(100, env="SYNC_BATCH_SIZE")  # Registros por lote
    change_threshold_percentage: float = Field(5.0, env="SYNC_CHANGE_THRESHOLD")  # 5% mínimo cambio
    change_threshold_units: int = Field(10, env="SYNC_CHANGE_THRESHOLD_UNITS")  # 10 unidades mínimo
    max_parallel_batches: int = Field(3, env="SYNC_MAX_PARALLEL_BATCHES")
    
    # Horarios de sincronización
    daily_sync_hour: int = Field(2, env="SYNC_DAILY_HOUR")  # 2:00 AM como mencionaste
    daily_sync_minute: int = Field(0, env="SYNC_DAILY_MINUTE")
    
    # Configuración de reintentos
    max_sync_retries: int = Field(3, env="SYNC_MAX_RETRIES")
    retry_delay_minutes: int = Field(30, env="SYNC_RETRY_DELAY_MINUTES")


class LoggingConfig(BaseSettings):
    """Configuración del sistema de logging"""
    level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    json_format: bool = Field(True, env="LOG_JSON_FORMAT")
    
    # Archivos de log
    log_dir: str = Field("logs", env="LOG_DIR")
    log_filename: str = Field("inventory_sync.log", env="LOG_FILENAME")
    max_file_size_mb: int = Field(50, env="LOG_MAX_FILE_SIZE_MB")
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # Logging específico por componente
    erp_log_level: LogLevel = Field(LogLevel.INFO, env="ERP_LOG_LEVEL")
    shopify_log_level: LogLevel = Field(LogLevel.INFO, env="SHOPIFY_LOG_LEVEL")
    database_log_level: LogLevel = Field(LogLevel.WARNING, env="DB_LOG_LEVEL")


class ApplicationConfig(BaseSettings):
    """Configuración principal de la aplicación"""
    app_name: str = Field("Inventory Sync App", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    environment: Environment = Field(Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Configuraciones anidadas
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    erp: ERPConfig = ERPConfig()
    shopify: ShopifyConfig = ShopifyConfig()
    sync: SyncConfig = SyncConfig()
    logging: LoggingConfig = LoggingConfig()
    
    # Configuración de monitoreo
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(8080, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment")
    def validate_environment(cls, v):
        """Valida que el ambiente sea válido"""
        if v not in Environment:
            raise ValueError(f"Environment must be one of: {list(Environment)}")
        return v
    
    @validator("debug")
    def set_debug_based_on_env(cls, v, values):
        """Activa debug automáticamente en development"""
        if values.get("environment") == Environment.DEVELOPMENT:
            return True
        return v


# Instancia global de configuración
config = ApplicationConfig()


def get_config() -> ApplicationConfig:
    """
    Función helper para obtener la configuración
    Útil para inyección de dependencias
    """
    return config


def reload_config() -> ApplicationConfig:
    """
    Recarga la configuración desde las variables de entorno
    Útil para testing o cambios en runtime
    """
    global config
    config = ApplicationConfig()
    return config