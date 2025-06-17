from domain.repositories.ISyncLogRepository import ISyncLogRepository

class PostgreSQLSyncLogRepository(ISyncLogRepository):
    """ IMPLEMENTACION CONCRETA: PostgreSQL para inventario """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def create_sync_log(self, sync_log):
        return await super().create_sync_log(sync_log)
    
    async def _get_connection(self):
        """ Obtiene una conexion nueva o crea una """


