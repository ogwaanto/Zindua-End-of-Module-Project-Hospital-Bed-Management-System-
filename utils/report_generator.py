from database.db_handler import DatabaseHandler


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
