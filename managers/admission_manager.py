from datetime import datetime
from database.db_handler import DatabaseHandler
from managers.bed_manager import BedManager


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
