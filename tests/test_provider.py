import hashlib
import unittest

from faker import Faker
from faker_graphics import Provider


class TestRandomColor(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Faker.seed(42)

    def setUp(self):
        self.faker = Faker()
        self.faker.add_provider(Provider)

    def test_placeholder_image(self):
        value = self.faker.placeholder_image(hue="blue")
        self.assertTrue(value.startswith(b"\x89PNG\r\n"))
        self.assertEqual(len(value), 3473)
        self.assertEqual(
            hashlib.sha256(value).hexdigest(),
            "544f87e42c4760563b1345ec96086bc323368edd9545f1985bada26d58b334a3",
        )

        # next call with the same arguments results in a different image
        next_value = self.faker.placeholder_image(hue="blue")
        self.assertNotEqual(value, next_value)

        # with open('test.png', 'wb+') as fh:
        #     fh.write(value)
