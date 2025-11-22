from database.db_handler import DatabaseHandler
from datetime import datetime
import json
from pathlib import Path


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
