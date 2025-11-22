import hashlib
from database.db_handler import DatabaseHandler


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
