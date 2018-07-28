import unittest
from typing import List
import MultiFieldLookupCore.MultiFieldLookup as Core
import collections


message = collections.namedtuple('Message', 'keys text')
messages: List[message] = []


def process_return_values(keys: List[str], left_data, right_data):
    if right_data is None:
        messages.append(message(keys, "no matching right records"))
    else:
        messages.append(message(keys, "matching right records"))


def prep_looker() -> Core.Looker:
    messages.clear()
    return Core.Looker(process_return_values)


class MultiFieldLookupTests(unittest.TestCase):

    def test_create_looker(self):
        looker = prep_looker()
        looker.callback(['Test 1'], 'a', None)
        looker.callback(['Test 2'], 'a', 'b')
        self.assertEqual('no matching right records', messages[0].text)
        self.assertEqual('matching right records', messages[1].text)

    def test_push_single_matching_records(self):
        looker = prep_looker()
        looker.push_left(['a'], 'a')
        self.assertEqual(0, len(messages))
        looker.push_right(['a'], 'The letter a')
        self.assertEqual(1, len(messages))
        self.assertEqual('matching right records', messages[0].text)

    def test_push_single_unmatching_records(self):
        looker = prep_looker()
        looker.push_left(['a'], 'a')
        looker.push_right(['b'], 'b')
        self.assertEqual(1, len(messages))
        self.assertEqual('no matching right records', messages[0].text)

    def test_push_multiple_matching_records(self):
        looker = prep_looker()
        looker.push_left(['a'], 'a1')
        looker.push_left(['a'], 'a2')
        looker.push_left(['b'], 'b')
        self.assertEqual(0, len(messages))

        looker.push_right(['a'], 'The letter a')
        self.assertEqual(2, len(messages))
        self.assertEqual('matching right records', messages[0].text)
        self.assertEqual('matching right records', messages[1].text)

        looker.push_right(['b'], 'The letter b')
        self.assertEqual(3, len(messages))
        self.assertEqual('matching right records', messages[2].text)

    def test_push_multiple_unmatched_records(self):
        looker = prep_looker()
        looker.push_left(['a'], 'a1')
        looker.push_left(['a'], 'a2')
        looker.push_left(['b'], 'b')
        self.assertEqual(0, len(messages))

        looker.push_right(['b'], 'The letter b')
        self.assertEqual(3, len(messages))
        self.assertEqual('no matching right records', messages[0].text)
        self.assertEqual('no matching right records', messages[1].text)
        self.assertEqual('matching right records', messages[2].text)

    def test_close_right(self):
        looker = prep_looker()
        looker.push_left(['a'], 'a1')
        looker.close_right()
        self.assertEqual(1, len(messages))
        self.assertEqual('no matching right records', messages[0].text)

    def test_close_left(self):
        looker = prep_looker()
        looker.push_right(['b'], 'The letter b')
        looker.close_left()
        self.assertEqual(0, len(messages))
        self.assertEqual(0, len(looker.rightData))
        looker.push_right(['c'], 'The letter c')
        self.assertEqual(0, len(messages))
        self.assertEqual(0, len(looker.rightData))

    def test_close_left_with_stragglers(self):
        looker = prep_looker()
        looker.push_left(['c'], 'c')
        looker.close_left()
        self.assertEqual(0, len(messages))

        looker.push_right(['a'], 'The letter a')
        self.assertEqual(0, len(messages))
        self.assertEqual(0, len(looker.rightData))

        looker.push_right(['c'], 'The letter c')
        self.assertEqual(1, len(messages))
        self.assertEqual('matching right records', messages[0].text)

    def test_close_left_with_stragglers_unmatched(self):
        looker = prep_looker()
        looker.push_left(['c'], 'c')
        looker.close_left()
        self.assertEqual(0, len(messages))

        looker.push_right(['a'], 'The letter a')
        self.assertEqual(0, len(messages))
        self.assertEqual(0, len(looker.rightData))

        looker.push_right(['d'], 'The letter d')
        self.assertEqual(1, len(messages))
        self.assertEqual('no matching right records', messages[0].text)

    def test_close_left_with_stragglers_close_right(self):
        looker = prep_looker()
        looker.push_left(['c'], 'c')
        looker.close_left()
        self.assertEqual(0, len(messages))

        looker.close_right()
        self.assertEqual(1, len(messages))
        self.assertEqual('no matching right records', messages[0].text)


if __name__ == '__main__':
    unittest.main()
