"""
Sistema de configuración centralizado usando Pydantic
Ubicación: src/shared/config/config_manager.py
"""

import os
from typing import Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    host: str = Field(..., description="Host de la base de datos")
    port: int = Field(5432, description="Puerto de la base de datos")
    name: str = Field(..., description="Nombre de la base de datos")
    user: str = Field(..., description="Usuario de la base de datos")
    password: str = Field(..., description="Contraseña de la base de datos")
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a la base de datos"""
        return f"postgresql://{self.user}:{self.password}@{self.host}/{self.name}"


class ERPConfig(BaseSettings):
    """Configuración del ERP"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    endpoint_url: str = Field(..., description="URL del endpoint del ERP")
    api_key: Optional[str] = Field(None, description="API Key del ERP")


class ShopifyConfig(BaseSettings):
    """Configuración de Shopify"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    access_token: str = Field(..., description="Token de acceso de Shopify")
    shop_domain: str = Field(..., description="Dominio de la tienda Shopify")


class LoggingConfig(BaseSettings):
    """Configuración del sistema de logging"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    level: LogLevel = Field(LogLevel.INFO, description="Nivel de logging general")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Formato del log"
    )
    json_format: bool = Field(True, description="Usar formato JSON para logs")
    
    # Archivos de log
    log_dir: str = Field("logs", description="Directorio para archivos de log")
    log_filename: str = Field("inventory_sync.log", description="Nombre del archivo de log")
    max_file_size_mb: int = Field(50, description="Tamaño máximo del archivo de log en MB")
    backup_count: int = Field(5, description="Número de archivos de backup")
    
    # Logging específico por componente
    erp_log_level: LogLevel = Field(LogLevel.INFO, description="Nivel de log para ERP")
    shopify_log_level: LogLevel = Field(LogLevel.INFO, description="Nivel de log para Shopify")
    database_log_level: LogLevel = Field(LogLevel.WARNING, description="Nivel de log para base de datos")


class ApplicationConfig(BaseSettings):
    """Configuración principal de la aplicación"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    app_name: str = Field("Inventory Sync App", description="Nombre de la aplicación")
    app_version: str = Field("1.0.0", description="Versión de la aplicación")
    environment: Environment = Field(Environment.DEVELOPMENT, description="Ambiente de ejecución")
    debug: bool = Field(False, description="Modo debug")
    
    # Variables de entorno para cada configuración
    # Database
    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    
    # ERP
    erp_endpoint_url: str = Field(..., alias="ERP_ENDPOINT_URL")
    erp_api_key: Optional[str] = Field(None, alias="ERP_API_KEY")
    
    # Shopify
    shopify_access_token: str = Field(..., alias="SHOPIFY_ACCESS_TOKEN")
    shopify_shop_domain: str = Field(..., alias="SHOPIFY_SHOP_DOMAIN")
    
    # Logging
    log_level: LogLevel = Field(LogLevel.INFO, alias="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="LOG_FORMAT"
    )
    log_json_format: bool = Field(True, alias="LOG_JSON_FORMAT")
    log_dir: str = Field("logs", alias="LOG_DIR")
    log_filename: str = Field("inventory_sync.log", alias="LOG_FILENAME")
    log_max_file_size_mb: int = Field(50, alias="LOG_MAX_FILE_SIZE_MB")
    log_backup_count: int = Field(5, alias="LOG_BACKUP_COUNT")
    erp_log_level: LogLevel = Field(LogLevel.INFO, alias="ERP_LOG_LEVEL")
    shopify_log_level: LogLevel = Field(LogLevel.INFO, alias="SHOPIFY_LOG_LEVEL")
    database_log_level: LogLevel = Field(LogLevel.WARNING, alias="DB_LOG_LEVEL")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Valida que el ambiente sea válido"""
        if v not in [env.value for env in Environment]:
            raise ValueError(f"Environment must be one of: {[env.value for env in Environment]}")
        return v
    
    @field_validator("debug")
    @classmethod
    def set_debug_based_on_env(cls, v, info):
        """Activa debug automáticamente en development"""
        if info.data.get("environment") == Environment.DEVELOPMENT:
            return True
        return v
    
    @property
    def database(self) -> DatabaseConfig:
        """Configuración de base de datos"""
        return DatabaseConfig(
            host=self.db_host,
            port=self.db_port,
            name=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    @property
    def erp(self) -> ERPConfig:
        """Configuración del ERP"""
        return ERPConfig(
            endpoint_url=self.erp_endpoint_url,
            api_key=self.erp_api_key
        )
    
    @property
    def shopify(self) -> ShopifyConfig:
        """Configuración de Shopify"""
        return ShopifyConfig(
            access_token=self.shopify_access_token,
            shop_domain=self.shopify_shop_domain
        )
    
    @property
    def logging(self) -> LoggingConfig:
        """Configuración de logging"""
        return LoggingConfig(
            level=self.log_level,
            format=self.log_format,
            json_format=self.log_json_format,
            log_dir=self.log_dir,
            log_filename=self.log_filename,
            max_file_size_mb=self.log_max_file_size_mb,
            backup_count=self.log_backup_count,
            erp_log_level=self.erp_log_level,
            shopify_log_level=self.shopify_log_level,
            database_log_level=self.database_log_level
        )


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


def print_config_status():
    """
    Función de debug para verificar qué variables se están cargando
    """
    print("=== CONFIGURACIÓN ACTUAL ===")
    # print(f"Environment: {config.environment}")
    # print(f"Debug: {config.debug}")
    # print(f"DB Host: {config.db_host}")
    # print(f"ERP Endpoint: {config.erp_endpoint_url}")
    # print(f"Shopify Domain: {config.shopify_shop_domain}")
    # print(f"Log Level: {config.log_level}")
    print(config.shopify.access_token, config.shopify.shop_domain)
    print(config.erp)
    print(config.database)
    print("==========================")