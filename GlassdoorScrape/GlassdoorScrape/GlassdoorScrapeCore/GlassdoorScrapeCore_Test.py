import unittest
import GlassdoorScrapeCore.GlassdoorScrapeCore as core

class MyTestCase(unittest.TestCase):
    def test_something(self):
        result = core.getReviews("Alteryx", 1)
        self.assertEqual(10, len(result.reviews))
        self.assertEqual('E351220', result.GlassdoorId)

if __name__ == '__main__':
    unittest.main()
