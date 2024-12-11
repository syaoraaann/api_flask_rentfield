"""DB Helper"""
import os
from mysql.connector.pooling import MySQLConnectionPool

# Membaca konfigurasi dari environment variables
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'rent_field')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_POOLNAME = os.environ.get('DB_POOLNAME', 'default_pool')
POOL_SIZE = int(os.environ.get('POOL_SIZE', 10))

# Membuat koneksi pool
db_pool = MySQLConnectionPool(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    pool_size=POOL_SIZE,
    pool_name=DB_POOLNAME
)

def get_connection():
    """
    Mendapatkan koneksi dari pool
    """
    connection = db_pool.get_connection()
    connection.autocommit = True
    return connection