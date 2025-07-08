#!/usr/bin/env python3
import sys
import os
import asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import signal

import logging

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.main import main as sync_inventory
from src.shared.config.config_manager import get_config, print_config_status


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def job_wrapper():
    """Wrapper para la función de sincronización con manejo de errores"""
    try:
        logger.info("Iniciando sincronización de inventario...")
        config = get_config()
        #print_config_status()
        asyncio.run(sync_inventory(config=config))
        logger.info("Sincronización completada exitosamente")
    except Exception as e:
        logger.error(f"Error durante la sincronización: {str(e)}")

def signal_handler(signum, frame):
    """Maneja las señales de terminación"""
    logger.info("Recibida señal de terminación. Cerrando scheduler...")
    scheduler.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    # Crear scheduler
    scheduler = BlockingScheduler()
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configurar horarios específicos de ejecución
    # Puedes modificar estos horarios según tus necesidades
    sync_times = [
        {'hour': 9, 'minute': 30},   # 9:30 AM
        {'hour': 13, 'minute': 0},   # 1:00 PM
        {'hour': 16, 'minute': 30},  # 4:30 PM
        {'hour': 19, 'minute': 45}   # 7:30 PM
    ]
    
    # Agregar un job para cada horario
    for i, time_config in enumerate(sync_times):
        scheduler.add_job(
            job_wrapper,
            CronTrigger(
                hour=time_config['hour'],
                minute=time_config['minute'],
                timezone='America/Mexico_City'  # Ajusta según tu zona horaria
            ),
            id=f'inventory_sync_{i}',
            name=f'Sincronización {time_config["hour"]:02d}:{time_config["minute"]:02d}',
            replace_existing=True
        )
    
    # Mostrar los horarios programados
    schedule_times = [f"{t['hour']:02d}:{t['minute']:02d}" for t in sync_times]
    logger.info(f"Scheduler iniciado. Ejecutará en los horarios: {', '.join(schedule_times)}")
    logger.info("Presiona Ctrl+C para detener")
    
    # Opcional: Ejecutar una vez al inicio solo si no hay ejecución programada pronto
    from datetime import datetime, time as dt_time
    import pytz
    
    # Verificar si hay alguna ejecución programada en los próximos 30 minutos
    now = datetime.now(pytz.timezone('America/Mexico_City'))
    should_run_now = True
    
    for time_config in sync_times:
        scheduled_time = now.replace(
            hour=time_config['hour'], 
            minute=time_config['minute'], 
            second=0, 
            microsecond=0
        )
        
        # Si hay una ejecución programada en los próximos 30 minutos, no ejecutar ahora
        time_diff = (scheduled_time - now).total_seconds()
        if 0 < time_diff < 1800:  # 30 minutos = 1800 segundos
            should_run_now = False
            logger.info(f"Próxima ejecución programada en {int(time_diff/60)} minutos. Esperando...")
            break
    
    if should_run_now:
        logger.info("Ejecutando sincronización inicial...")
        job_wrapper()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler detenido por el usuario")
    except Exception as e:
        logger.error(f"Error en el scheduler: {str(e)}")
    finally:
        scheduler.shutdown()
        logger.info("Scheduler cerrado")
   