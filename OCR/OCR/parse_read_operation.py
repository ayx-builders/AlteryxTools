import json
from typing import List


class Line:
    def __init__(self, page: int, clockwise_orientation: float, page_width: float, page_height: float, unit: str, text: str, top_left_x, top_left_y, top_right_x, top_right_y, bottom_right_x, bottom_right_y, bottom_left_x, bottom_left_y):
        self.page = page
        self.clockwiseOrientation = clockwise_orientation
        self.pageWidth = page_width
        self.pageHeight = page_height
        self.unit = unit
        self.text = text
        self.topLeftX = top_left_x
        self.topLeftY = top_left_y
        self.topRightX = top_right_x
        self.topRightY = top_right_y
        self.bottomRightX = bottom_right_x
        self.bottomRightY = bottom_right_y
        self.bottomLeftX = bottom_left_x
        self.bottomLeftY = bottom_left_y


def parse_recognition_results(recognition_results: json) -> List[Line]:
    lines: List[Line] = []
    for page in recognition_results:
        for text in page['lines']:
            box = text['boundingBox']
            line = Line(page['page'], page['clockwiseOrientation'], page['width'], page['height'], page['unit'], text['text'], box[0], box[1], box[2], box[3], box[4], box[5], box[6], box[7])
            lines.append(line)
    return lines
