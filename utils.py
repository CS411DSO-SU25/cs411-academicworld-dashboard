import dash
from dash import html, dcc, dash_table, callback_context
from dash.dependencies import Input, Output, State
import mysql.connector.pooling
from pymongo import MongoClient
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import math
import dash.exceptions as dash_exceptions
import re


mysql_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host="127.0.0.1",
    user="root",
    password="furbat11",
    database="academicworld",
    auth_plugin="mysql_native_password"
)

mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client.academicworld

NEO4J_URL = "http://localhost:7474/db/academicworld/tx/commit"
AUTH = HTTPBasicAuth("neo4j", "furbat11")
HEADERS = {"Content-Type": "application/json"}

def get_mysql_cursor():
    """
    Get a MySQL connection and cursor from the pool.
    IMPORTANT: Always call both cursor.close() and conn.close() after use to avoid connection leaks!
    Returns (conn, cursor)
    """
    conn = mysql_pool.get_connection()
    cursor = conn.cursor(prepared=True)
    return conn, cursor

def sanitize_input(val, max_length=100):
    """Sanitize dropdown or text input from the user."""
    if val is None:
        return None
    val = str(val).strip()
    val = val[:max_length]
    val = re.sub(r"[^\w\s\-.']", "", val, flags=re.UNICODE)
    return val