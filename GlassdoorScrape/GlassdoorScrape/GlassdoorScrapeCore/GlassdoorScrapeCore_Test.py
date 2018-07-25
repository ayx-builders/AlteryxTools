import unittest
import GlassdoorScrapeCore.GlassdoorScrapeCore as Core


class MyTestCase(unittest.TestCase):

    def test_CompanyNameSearch(self):
        result = Core.search_company_name("slalom")
        self.assertEqual('Slalom', result.GlassdoorName)
        self.assertEqual('E31102', result.GlassdoorId)
        self.assertEqual(True, result.found)

        result = Core.search_company_name('sflktljldsv')
        self.assertEqual('', result.GlassdoorName)
        self.assertEqual('', result.GlassdoorId)
        self.assertEqual(False, result.found)

        result = Core.search_company_name("KPMG")
        self.assertEqual("KPMG", result.GlassdoorName)
        self.assertEqual('E2867', result.GlassdoorId)
        self.assertEqual(True, result.found)

    def test_Complete(self):
        result = Core.get_company_data("Alteryx", 1)
        self.assertEqual(10, len(result.reviews))
        self.assertEqual('E351220', result.GlassdoorId)


if __name__ == '__main__':
    unittest.main()
