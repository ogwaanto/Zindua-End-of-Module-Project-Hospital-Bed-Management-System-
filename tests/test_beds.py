import unittest
import os
from main import DatabaseHandler, BedManager


class TestBedManager(unittest.TestCase):
    def setUp(self):
        # use in-memory sqlite for isolation
        self.db = DatabaseHandler(":memory:")
        self.db.initialize_db()
        self.bm = BedManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass

    def test_add_and_list(self):
        self.bm.add_bed("ICU", ["O2", "Monitor"])
        beds = self.bm.list_beds()
        self.assertEqual(len(beds), 1)
        bed = beds[0]
        self.assertEqual(bed["ward_type"], "ICU")
        self.assertEqual(bed["status"], "available")

    def test_assign_and_free(self):
        self.bm.add_bed("HDU", [])
        bed = self.bm.get_available_beds()[0]
        self.bm.assign_bed(bed["bed_id"])
        avail = self.bm.get_available_beds()
        self.assertEqual(len(avail), 0)
        self.bm.free_bed(bed["bed_id"])
        avail2 = self.bm.get_available_beds()
        self.assertEqual(len(avail2), 1)


if __name__ == "__main__":
    unittest.main()
