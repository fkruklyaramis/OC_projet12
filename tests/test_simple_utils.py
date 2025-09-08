import unittest
from src.utils.hash_utils import hash_password, verify_password
from src.utils.auth_utils import generate_employee_number


class TestUtils(unittest.TestCase):

    def test_hash_password_basic(self):
        password = "test123"
        hashed = hash_password(password)
        self.assertIsNotNone(hashed)
        self.assertNotEqual(hashed, password)

    def test_verify_password_basic(self):
        password = "test123"
        hashed = hash_password(password)
        result = verify_password(hashed, password)
        self.assertTrue(result)

    def test_generate_employee_number_basic(self):
        emp_num = generate_employee_number()
        self.assertEqual(len(emp_num), 8)  # "EE" + 6 chiffres
        self.assertTrue(emp_num.startswith("EE"))  # Commence par "EE"
        self.assertTrue(emp_num[2:].isdigit())  # Les 6 derniers caractères sont des chiffres
