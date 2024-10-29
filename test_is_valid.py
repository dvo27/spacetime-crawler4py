import unittest
from scraper import is_valid

class TestIsValidFunction(unittest.TestCase):

    def test_valid_domains(self):
        # Test URLs within the valid domains
        self.assertTrue(is_valid("https://www.ics.uci.edu/somepage"))
        self.assertTrue(is_valid("http://cs.uci.edu/home"))
        self.assertTrue(is_valid("https://informatics.uci.edu/about"))
        self.assertTrue(is_valid("https://stat.uci.edu/contact"))
        self.assertTrue(is_valid("https://today.uci.edu/department/information_computer_sciences/news"))

    def test_invalid_domains(self):
        # Test URLs outside of the specified domains
        self.assertFalse(is_valid("https://www.otherdomain.uci.edu"))
        self.assertFalse(is_valid("https://www.google.com"))
        self.assertFalse(is_valid("https://today.uci.edu/otherdepartment"))

    def test_invalid_file_extensions(self):
        # Test URLs with excluded file extensions
        self.assertFalse(is_valid("https://www.ics.uci.edu/image.jpg"))
        self.assertFalse(is_valid("https://cs.uci.edu/document.pdf"))
        self.assertFalse(is_valid("https://informatics.uci.edu/video.mp4"))

    def test_invalid_schemes(self):
        # Test URLs with unsupported schemes
        self.assertFalse(is_valid("ftp://www.ics.uci.edu"))
        self.assertFalse(is_valid("mailto:info@ics.uci.edu"))

if __name__ == "__main__":
    unittest.main()