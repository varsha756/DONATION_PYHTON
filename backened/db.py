import mysql.connector

def connect_db():
    try:
        conn = mysql.connector.connect(
        import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "donation_checker.db")

def connect_db():
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _init_tables(conn)
        return conn
    except sqlite3.Error as err:
        print("❌ Error:", err)
        return None

def _init_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT,
            is_verified BOOLEAN DEFAULT 0,
            verification_code TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ngos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            transparency_score REAL DEFAULT 0,
            image_path TEXT,
            upi_id TEXT,
            total_received REAL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_email TEXT,
            ngo_id INTEGER,
            amount REAL,
            payment_proof_path TEXT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ngo_id) REFERENCES ngos(id)
        )
    """)
    conn.commit()    host="localhost",
            user="root",
            password="vasu06",
            database="donation_checker"
        )
        return conn
    except mysql.connector.Error as err:
        print("❌ Error:", err)
        return None