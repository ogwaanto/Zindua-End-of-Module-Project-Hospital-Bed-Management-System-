from models.bed import Bed
from database.db_handler import DatabaseHandler


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
