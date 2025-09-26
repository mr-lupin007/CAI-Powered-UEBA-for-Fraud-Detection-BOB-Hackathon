import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
load_dotenv()

DSN = os.getenv("DB_DSN")

def get_conn():
    return psycopg2.connect(DSN, cursor_factory=RealDictCursor)
