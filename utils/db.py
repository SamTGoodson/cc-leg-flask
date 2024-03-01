import psycopg2
from .config import psql_user, psql_pass


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='city-council',
                            user=psql_user,
                            password=psql_pass)
    return conn


