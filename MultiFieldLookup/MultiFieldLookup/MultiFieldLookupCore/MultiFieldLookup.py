from typing import List
import collections


record = collections.namedtuple('record', 'keys data')


class Looker:
    def __init__(self, lookup_callback):
        self.callback = lookup_callback
        self.leftData: List[record] = []
        self.rightData: List[record] = []
        self.leftClosed: bool = False
        self.rightClosed: bool = False

    def push_left(self, keys: List, data: object):
        self.leftData.append(record(keys, data))
        self.check_records()

    def push_right(self, keys: List, data: object):
        if not self.leftClosed or len(self.leftData) > 0:
            self.rightData.append(record(keys, data))
            self.check_records()

    def close_right(self):
        self.rightClosed = True
        self.check_records()

    def close_left(self):
        self.leftClosed = True
        self.check_records()

    def check_records(self):
        if len(self.leftData) == 0 and self.leftClosed:
            self.rightData.clear()
            return

        if len(self.leftData) > 0 and (len(self.rightData) > 0 or self.rightClosed):
            if len(self.rightData) == 0:
                while len(self.leftData) > 0:
                    left_record = self.leftData[0]
                    self.callback(left_record.keys, left_record.data, None)
                    self.leftData.remove(left_record)
                return

            left_index = 0
            while left_index < len(self.leftData):
                increment_left = True
                left_record = self.leftData[left_index]
                while len(self.rightData) > 0:
                    right_record = self.rightData[0]

                    if left_record.keys <= right_record.keys:
                        if left_record.keys == right_record.keys:
                            right_data = right_record.data
                        else:
                            right_data = None

                        self.callback(left_record.keys, left_record.data, right_data)
                        self.leftData.remove(left_record)
                        increment_left = False
                        break
                    else:
                        self.rightData.remove(right_record)

                if increment_left:
                    left_index = left_index + 1
