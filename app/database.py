import mysql.connector
from mysql.connector import pooling, Error
from app.config import settings

class DatabaseManager:
    """Maneja el Pool de conexiones hacia Amazon RDS MySQL."""
    def __init__(self):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="iot_pool",
            pool_size=5,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            autocommit=False  # Requerido para transacciones explícitas
        )

    def get_connection(self):
        try:
            return self.pool.get_connection()
        except Error as err:
            raise RuntimeError(f"Error de conexión a RDS: {err}")

db_manager = DatabaseManager()