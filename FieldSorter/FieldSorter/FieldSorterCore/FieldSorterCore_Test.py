import unittest
from typing import List
from FieldSorterCore.FieldSorterCore import sort_fields, Translation, SortItem


class FieldSorterTest(unittest.TestCase):
    def test_reverse_order(self):
        self.sort_abc(gen_items(['C', 'B', 'A']), [(2, 0, 'C'), (1, 1, 'B'), (0, 2, 'A')])

    def test_first_field_no_match(self):
        self.sort_abc(gen_items(['B', 'C']), [(1, 0, 'B'), (2, 1, 'C'), (0, 2, 'A')])

    def test_no_changes(self):
        self.sort_abc([], [(0, 0, 'A'), (1, 1, 'B'), (2, 2, 'C')])

    def test_pattern(self):
        self.sort_abc([SortItem('C|B', True), SortItem('A')], [(1, 0, 'B'), (2, 1, 'C'), (0, 2, 'A')])

    def test_no_matches(self):
        self.sort_abc(gen_items(['G', 'C', 'H', 'B']), [(2, 0, 'C'), (1, 1, 'B'), (0, 2, 'A')])

    def test_duplicate_matches(self):
        self.sort_abc(gen_items(['B', 'B', 'B', 'C', 'A']), [(1, 0, 'B'), (2, 1, 'C'), (0, 2, 'A')])

    def test_alphabetical_sort(self):
        source: List[str] = ['Z', 'Y', 'X']
        change_to: List[SortItem] = gen_items(['X'])
        new_order = sort_fields(source, change_to, alphabetical=True)
        self.assertEqual([(2, 0, 'X'), (1, 1, 'Y'), (0, 2, 'Z')], new_order)

    def sort_abc(self, change_to: List[SortItem], result: List[Translation]):
        source: List[str] = ['A', 'B', 'C']
        new_order = sort_fields(source, change_to)
        self.assertEqual(result, new_order)


def gen_items(fields: List[str]) -> List[SortItem]:
    sort_items: List[SortItem] = []
    for field in fields:
        sort_items.append(SortItem(field))
    return sort_items


if __name__ == '__main__':
    unittest.main()
