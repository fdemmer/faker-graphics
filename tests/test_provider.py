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
        self.assertTrue(len(value) >= 3300)

        # next call with the same arguments results in a different image
        next_value = self.faker.placeholder_image(hue="blue")
        self.assertNotEqual(value, next_value)

        # with open('test.png', 'wb+') as fh:
        #     fh.write(value)
