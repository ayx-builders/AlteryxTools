import unittest
import GlassdoorScrapeCore.GlassdoorScrapeCore as core


class MyTestCase(unittest.TestCase):

    def test_companyNameSearch(self):
        result = core.searchCompanyName("slalom")
        self.assertEqual('Slalom', result.GlassdoorName)
        self.assertEqual('E31102', result.GlassdoorId)
        self.assertEqual(True, result.found)

        result = core.searchCompanyName('sflktljldsv')
        self.assertEqual('', result.GlassdoorName)
        self.assertEqual('', result.GlassdoorId)
        self.assertEqual(False, result.found)

        result = core.searchCompanyName("KPMG")
        self.assertEqual("KPMG", result.GlassdoorName)
        self.assertEqual('E2867', result.GlassdoorId)
        self.assertEqual(True, result.found)

    def test_Complete(self):
        result = core.getReviews("Alteryx", 1)
        self.assertEqual(10, len(result.reviews))
        self.assertEqual('E351220', result.GlassdoorId)


if __name__ == '__main__':
    unittest.main()
