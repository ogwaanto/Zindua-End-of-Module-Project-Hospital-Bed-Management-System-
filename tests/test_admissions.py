import unittest
from main import DatabaseHandler, BedManager, PatientManager, AdmissionManager


class TestAdmissionFlow(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        self.db.initialize_db()
        self.bm = BedManager(self.db)
        self.pm = PatientManager(self.db)
        self.am = AdmissionManager(self.db, self.bm)
        # create bed and patient
        self.bm.add_bed("ICU", [])
        self.pm.add_patient("Alice", 30, "Test")
        self.patient = self.db.fetch_one(
            "SELECT * FROM patients ORDER BY patient_id DESC LIMIT 1")
        self.bed = self.db.fetch_one(
            "SELECT * FROM beds ORDER BY bed_id DESC LIMIT 1")

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass

    def test_admit_and_discharge(self):
        adm = self.am.admit(self.patient["patient_id"], self.bed["bed_id"])
        self.assertIsNotNone(adm)
        self.assertIsNone(adm["date_out"])
        # ensure bed now occupied
        bedrow = self.db.fetch_one(
            "SELECT * FROM beds WHERE bed_id=?", (self.bed["bed_id"],))
        self.assertEqual(bedrow["status"], "occupied")
        # discharge
        dis = self.am.discharge(adm["admission_id"])
        self.assertIsNotNone(dis["date_out"])
        bedrow2 = self.db.fetch_one(
            "SELECT * FROM beds WHERE bed_id=?", (self.bed["bed_id"],))
        self.assertEqual(bedrow2["status"], "available")


if __name__ == "__main__":
    unittest.main()
