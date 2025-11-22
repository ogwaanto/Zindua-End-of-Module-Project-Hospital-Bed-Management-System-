from database.db_handler import DatabaseHandler
import os
from twilio.rest import Client


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
