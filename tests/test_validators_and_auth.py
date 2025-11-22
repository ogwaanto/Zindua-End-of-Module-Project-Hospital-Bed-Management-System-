import unittest
from main import Validators, DatabaseHandler, AuthManager


class TestValidatorsAuth(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        self.db.initialize_db()
        self.auth = AuthManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass

    def test_validators(self):
        self.assertTrue(Validators.validate_name("Alice Smith"))
        self.assertFalse(Validators.validate_name("Alice123"))
        self.assertTrue(Validators.validate_age("45"))
        self.assertFalse(Validators.validate_age("abc"))

    def test_user_create_and_auth(self):
        # create a user and authenticate
        self.auth.create_user("clerk1", "password", role="clerk")
        user = self.auth.authenticate("clerk1", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "clerk")
        # wrong pw
        self.assertIsNone(self.auth.authenticate("clerk1", "bad"))


if __name__ == "__main__":
    unittest.main()
