from database.db_handler import DatabaseHandler
import re


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
