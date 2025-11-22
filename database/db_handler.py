import sqlite3
import os
from pathlib import Path


class DatabaseHandler:
    def __init__(self, db_path="hospital.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        cur = self.cursor.execute(query, params)
        self.conn.commit()
        return cur

    def fetch_all(self, query, params=()):
        cur = self.cursor.execute(query, params)
        return cur.fetchall()

    def fetch_one(self, query, params=()):
        cur = self.cursor.execute(query, params)
        return cur.fetchone()

    def initialize_db(self):
        # Create tables if not exist
        schema = """
        CREATE TABLE IF NOT EXISTS beds (
            bed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            equipment TEXT
        );
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            diagnosis TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admissions (
            admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            bed_id INTEGER NOT NULL,
            date_in TEXT NOT NULL,
            date_out TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (bed_id) REFERENCES beds(bed_id)
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        );
        """
        self.cursor.executescript(schema)
        self.conn.commit()

    def close(self):
        self.conn.close()
