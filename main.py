#!/usr/bin/env python3

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import hashlib
import getpass
import re
import shutil

# Optional Twilio import - used only if env is configured.
try:
    from twilio.rest import Client
except Exception:
    # Twilio not required for tests; AlertManager handles this gracefully.
    Client = None


# ---------------------------
# Database Handler
# ---------------------------
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


# ---------------------------
# Validators (regex)
# ---------------------------
class Validators:
    NAME = re.compile(r'^[A-Za-z ]+$')
    AGE = re.compile(r'^\d{1,3}$')
    WARD = re.compile(r'^(ICU|HDU|Maternity|General)$')
    DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    @classmethod
    def validate_name(cls, name):
        return bool(cls.NAME.match(name))

    @classmethod
    def validate_age(cls, age):
        return bool(cls.AGE.match(str(age)))

    @classmethod
    def validate_ward(cls, ward):
        return bool(cls.WARD.match(ward))

    @classmethod
    def validate_date(cls, date_str):
        return bool(cls.DATE.match(date_str))


# ---------------------------
# Managers & Models
# ---------------------------
class BedManager:
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_bed(self, ward_type, equipment=None):
        equipment = ",".join(equipment or [])
        self.db.execute_query("INSERT INTO beds (ward_type, equipment) VALUES (?, ?)",
                              (ward_type, equipment))

    def list_beds(self):
        return self.db.fetch_all("SELECT * FROM beds ORDER BY bed_id")

    def get_available_beds(self, ward_type=None):
        if ward_type:
            return self.db.fetch_all("SELECT * FROM beds WHERE status='available' AND ward_type=?",
                                     (ward_type,))
        return self.db.fetch_all("SELECT * FROM beds WHERE status='available'")

    def assign_bed(self, bed_id):
        bed = self.db.fetch_one("SELECT * FROM beds WHERE bed_id=?", (bed_id,))
        if not bed:
            raise ValueError("Bed not found")
        if bed['status'] == 'occupied':
            raise ValueError("Bed already occupied")
        self.db.execute_query(
            "UPDATE beds SET status='occupied' WHERE bed_id=?", (bed_id,))

    def free_bed(self, bed_id):
        bed = self.db.fetch_one("SELECT * FROM beds WHERE bed_id=?", (bed_id,))
        if not bed:
            raise ValueError("Bed not found")
        self.db.execute_query(
            "UPDATE beds SET status='available' WHERE bed_id=?", (bed_id,))

    def search_beds(self, ward_type=None, equipment=None, available_only=False):
        sql = "SELECT * FROM beds WHERE 1=1"
        params = []
        if ward_type:
            sql += " AND ward_type=?"
            params.append(ward_type)
        if equipment:
            sql += " AND equipment LIKE ?"
            params.append(f"%{equipment}%")
        if available_only:
            sql += " AND status='available'"
        return self.db.fetch_all(sql, tuple(params))


class PatientManager:
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_patient(self, name, age, diagnosis):
        self.db.execute_query("INSERT INTO patients (name, age, diagnosis) VALUES (?, ?, ?)",
                              (name, int(age), diagnosis))

    def find_patient_by_name(self, regex):
        rows = self.db.fetch_all("SELECT * FROM patients")
        pat = re.compile(regex)
        return [r for r in rows if pat.search(r['name'])]

    def get_patient(self, patient_id):
        return self.db.fetch_one("SELECT * FROM patients WHERE patient_id=?", (patient_id,))

    def list_patients(self):
        return self.db.fetch_all("SELECT * FROM patients ORDER BY patient_id")


class AdmissionManager:
    def __init__(self, db: DatabaseHandler, bed_manager: BedManager):
        self.db = db
        self.bed_manager = bed_manager

    def admit(self, patient_id, bed_id, date_in=None):
        date_in = date_in or datetime.now().strftime("%Y-%m-%d")
        # ensure bed exists and is available
        bed = self.db.fetch_one("SELECT * FROM beds WHERE bed_id=?", (bed_id,))
        if not bed:
            raise ValueError("Bed not found")
        if bed['status'] == 'occupied':
            raise ValueError("Bed is occupied")
        self.db.execute_query("INSERT INTO admissions (patient_id, bed_id, date_in) VALUES (?, ?, ?)",
                              (patient_id, bed_id, date_in))
        self.bed_manager.assign_bed(bed_id)
        # return admission row
        return self.db.fetch_one("SELECT * FROM admissions ORDER BY admission_id DESC LIMIT 1")

    def discharge(self, admission_id, date_out=None):
        date_out = date_out or datetime.now().strftime("%Y-%m-%d")
        adm = self.db.fetch_one(
            "SELECT * FROM admissions WHERE admission_id=?", (admission_id,))
        if not adm:
            raise ValueError("Admission not found")
        if adm['date_out']:
            raise ValueError("Already discharged")
        self.db.execute_query(
            "UPDATE admissions SET date_out=? WHERE admission_id=?", (date_out, admission_id))
        # free bed
        self.bed_manager.free_bed(adm['bed_id'])
        return self.db.fetch_one("SELECT * FROM admissions WHERE admission_id=?", (admission_id,))

    def transfer(self, admission_id, new_bed_id):
        adm = self.db.fetch_one(
            "SELECT * FROM admissions WHERE admission_id=?", (admission_id,))
        if not adm:
            raise ValueError("Admission not found")
        if adm['date_out']:
            raise ValueError("Cannot transfer discharged patient")
        new_bed = self.db.fetch_one(
            "SELECT * FROM beds WHERE bed_id=?", (new_bed_id,))
        if not new_bed:
            raise ValueError("Target bed not found")
        if new_bed['status'] == 'occupied':
            raise ValueError("Target bed occupied")
        # free old bed and assign new bed
        self.bed_manager.free_bed(adm['bed_id'])
        self.bed_manager.assign_bed(new_bed_id)
        self.db.execute_query(
            "UPDATE admissions SET bed_id=? WHERE admission_id=?", (new_bed_id, admission_id))
        return self.db.fetch_one("SELECT * FROM admissions WHERE admission_id=?", (admission_id,))


# ---------------------------
# Auth Manager
# ---------------------------
class AuthManager:
    def __init__(self, db: DatabaseHandler):
        self.db = db

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, role="clerk"):
        ph = self.hash_password(password)
        self.db.execute_query("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                              (username, ph, role))

    def authenticate(self, username, password):
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username=?", (username,))
        if not row:
            return None
        if row['password_hash'] == self.hash_password(password):
            return dict(row)
        return None

    def ensure_admin_exists(self):
        admin = self.db.fetch_one("SELECT * FROM users WHERE role='admin'")
        if not admin:
            # create default admin with password 'admin' (for demo); in production prompt for secure pw
            self.create_user("admin", "admin", role="admin")
            return True
        return False


# ---------------------------
# Backup Manager
# ---------------------------
class BackupManager:
    def __init__(self, db: DatabaseHandler, backups_dir="backups", keep=7):
        self.db = db
        self.backups_dir = Path(backups_dir)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.keep = keep

    def create_backup(self):
        data = {}
        for table in ("beds", "patients", "admissions", "users"):
            rows = self.db.fetch_all(f"SELECT * FROM {table}")
            data[table] = [dict(r) for r in rows]
        date = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = self.backups_dir / f"{date}_backup.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        self.cleanup_backups()
        return path

    def cleanup_backups(self):
        files = sorted(self.backups_dir.glob("*_backup.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[self.keep:]:
            try:
                f.unlink()
            except Exception:
                pass

    def list_backups(self):
        return sorted(self.backups_dir.glob("*_backup.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# ---------------------------
# Alert Manager (Twilio placeholders)
# ---------------------------
class AlertManager:
    def __init__(self, db: DatabaseHandler):
        self.db = db
        sid = os.getenv("TWILIO_SID")
        token = os.getenv("TWILIO_TOKEN")
        from_phone = os.getenv("TWILIO_FROM")
        admin_phone = os.getenv("ADMIN_PHONE")
        self.from_phone = from_phone
        self.admin_phone = admin_phone
        self.enabled = False
        if sid and token and Client:
            try:
                self.client = Client(sid, token)
                self.enabled = True
            except Exception:
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False

    def _send_sms(self, to, message):
        if not self.enabled or not self.client:
            # Twilio not configured; print placeholder
            print("[AlertManager] Twilio not configured. Would send SMS to",
                  to, "message:", message)
            return None
        msg = self.client.messages.create(
            body=message, from_=self.from_phone, to=to)
        return getattr(msg, "sid", None)

    def alert_if_critical_full(self):
        # check ICU and HDU capacity and send alert if full
        for ward in ("ICU", "HDU"):
            total_row = self.db.fetch_one(
                "SELECT COUNT(*) as total FROM beds WHERE ward_type=?", (ward,))
            occupied_row = self.db.fetch_one(
                "SELECT SUM(CASE WHEN status='occupied' THEN 1 ELSE 0 END) as occupied FROM beds WHERE ward_type=?",
                (ward,))
            total = total_row['total'] if total_row else 0
            occupied = occupied_row['occupied'] or 0
            if total > 0 and occupied >= total:
                msg = f"CRITICAL: {ward} is full ({occupied}/{total})"
                if self.admin_phone:
                    self._send_sms(self.admin_phone, msg)
                else:
                    print("[AlertManager] Admin phone not set; alert:", msg)


# ---------------------------
# Undo Stack
# ---------------------------
class UndoStack:
    def __init__(self):
        self.stack = []

    def push(self, callable_fn, *args, **kwargs):
        self.stack.append((callable_fn, args, kwargs))

    def undo(self):
        if not self.stack:
            return None
        fn, args, kwargs = self.stack.pop()
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return e


# ---------------------------
# Report Generator (simple)
# ---------------------------
class ReportGenerator:
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def generate_occupancy(self):
        rows = self.db.fetch_all(
            "SELECT ward_type, COUNT(*) as total, SUM(CASE WHEN status='occupied' THEN 1 ELSE 0 END) as occupied FROM beds GROUP BY ward_type")
        return [dict(r) for r in rows]

    def list_free_beds(self):
        rows = self.db.fetch_all("SELECT * FROM beds WHERE status='available'")
        return [dict(r) for r in rows]


# ---------------------------
# CLI (guarded)
# ---------------------------
def main():
    db = DatabaseHandler(os.getenv("HOSP_DB", "hospital.db"))
    db.initialize_db()
    bed_mgr = BedManager(db)
    pat_mgr = PatientManager(db)
    adm_mgr = AdmissionManager(db, bed_mgr)
    auth = AuthManager(db)
    backup_mgr = BackupManager(db)
    alert_mgr = AlertManager(db)
    report = ReportGenerator(db)
    undo = UndoStack()

    # ensure at least one admin exists
    auth.ensure_admin_exists()

    # Login loop
    user = None
    while not user:
        print("=== Login ===")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        user = auth.authenticate(username, password)
        if not user:
            print("Invalid credentials, try again.\n")

    role = user["role"]
    print(f"Welcome {username} ({role})")

    while True:
        print("\n--- Menu ---")
        print("1. View available beds")
        print("2. Add bed")
        print("3. Admit patient")
        print("4. Transfer patient")
        print("5. Discharge patient")
        print("6. Search patients")
        print("7. Generate reports")
        print("8. Send alerts (check capacity)")
        print("9. Run backup")
        print("10. Undo last action")
        if role == "admin":
            print("11. Create user")
        print("0. Exit")

        choice = input("> ").strip()
        try:
            if choice == "1":
                beds = bed_mgr.list_beds()
                if not beds:
                    print("<no beds>")
                else:
                    for r in beds:
                        print(dict(r))
            elif choice == "2":
                if role != "admin":
                    print("Only admins can add beds")
                    continue
                ward = input("Ward (ICU/HDU/Maternity/General): ").strip()
                if not Validators.validate_ward(ward):
                    print("Invalid ward")
                    continue
                eq = input("Comma-separated equipment (or empty): ").strip().split(",") if input(
                    "Add equipment? (y/n) ").lower() == "y" else []
                bed_mgr.add_bed(ward, [e.strip() for e in eq if e.strip()])
                print("Bed added.")
            elif choice == "3":
                name = input("Patient name: ").strip()
                if not Validators.validate_name(name):
                    print("Invalid name")
                    continue
                age = input("Age: ").strip()
                if not Validators.validate_age(age):
                    print("Invalid age")
                    continue
                diag = input("Diagnosis: ").strip()
                pat_mgr.add_patient(name, age, diag)
                patient = db.fetch_one(
                    "SELECT * FROM patients ORDER BY patient_id DESC LIMIT 1")
                frees = bed_mgr.get_available_beds()
                if not frees:
                    print("No free beds")
                    continue
                print("Free beds:")
                for b in frees:
                    print(dict(b))
                bed_id = int(input("Enter bed_id to assign: ").strip())
                adm = adm_mgr.admit(patient["patient_id"], bed_id)
                # Push undo: discharge the admission

                def _undo_discharge(adm_mgr, adm_id):
                    # attempt to discharge (this will free bed) -- to undo an admit we discharge immediately
                    try:
                        adm_mgr.discharge(adm_id)
                        return True
                    except Exception as e:
                        return e
                undo.push(_undo_discharge, adm_mgr, adm["admission_id"])
                print("Patient admitted. Admission id:", adm["admission_id"])
            elif choice == "4":
                adm_id = int(input("Admission id: ").strip())
                new_bed = int(input("New bed id: ").strip())
                # save old bed for undo
                old = db.fetch_one(
                    "SELECT * FROM admissions WHERE admission_id=?", (adm_id,))
                if not old:
                    print("Admission not found")
                    continue
                adm_mgr.transfer(adm_id, new_bed)
                # push undo: transfer back
                undo.push(adm_mgr.transfer, adm_id, old["bed_id"])
                print("Transferred")
            elif choice == "5":
                adm_id = int(input("Admission id to discharge: ").strip())
                # push undo: re-admit (clear date_out and re-occupy bed)
                adm_row = db.fetch_one(
                    "SELECT * FROM admissions WHERE admission_id=?", (adm_id,))
                if not adm_row:
                    print("Admission not found")
                    continue
                if adm_row["date_out"]:
                    print("Already discharged")
                    continue
                adm_mgr.discharge(adm_id)
                # define undo: set date_out to NULL and reassign bed

                def _undo_reinstate(adm_mgr, db, admission_id):
                    row = db.fetch_one(
                        "SELECT * FROM admissions WHERE admission_id=?", (admission_id,))
                    if not row:
                        return "Admission row gone"
                    # set date_out to NULL and reassign bed
                    db.execute_query(
                        "UPDATE admissions SET date_out=NULL WHERE admission_id=?", (admission_id,))
                    # no-op to set attribute available to closure
                    adm_mgr.assign_bed = bed_mgr.assign_bed
                    bed_mgr.assign_bed(row["bed_id"])
                    return True
                undo.push(_undo_reinstate, adm_mgr, db, adm_id)
                print("Discharged")
            elif choice == "6":
                rx = input("Regex for patient name: ").strip()
                res = pat_mgr.find_patient_by_name(rx)
                if not res:
                    print("<no patients>")
                else:
                    for r in res:
                        print(dict(r))
            elif choice == "7":
                occ = report.generate_occupancy()
                print("Occupancy by ward:")
                for r in occ:
                    print(r)
                free = report.list_free_beds()
                print("Free beds count:", len(free))
            elif choice == "8":
                alert_mgr.alert_if_critical_full()
            elif choice == "9":
                if role != "admin":
                    print("Only admins can run backups")
                    continue
                path = backup_mgr.create_backup()
                print("Backup created at", path)
            elif choice == "10":
                res = undo.undo()
                print("Undo result:", res)
            elif choice == "11" and role == "admin":
                uname = input("New username: ")
                pw = getpass.getpass("Password: ")
                r = input("Role (admin/clerk): ")
                auth.create_user(uname, pw, role=r)
                print("User created")
            elif choice == "0":
                print("Goodbye")
                break
            else:
                print("Invalid option")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
