import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseManager():
    @staticmethod
    def getConnection():
        try:
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            print("Connection Successfull")
            
            return conn, cursor
        except Exception as e:
            print(e)
            return None, None
    @staticmethod
    def closeConnection(conn, cursor):
        if conn:
            conn = None
        if cursor:
            cursor = None
        print("Connection Closed")