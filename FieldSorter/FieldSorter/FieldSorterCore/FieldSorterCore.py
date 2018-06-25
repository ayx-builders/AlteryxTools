from typing import List, Tuple
from collections import namedtuple
import re


Translation = namedtuple('Translation', 'index_from index_to name')


class SortItem:
    def __init__(self, field: str, is_pattern: bool = False):
        self.field = field
        self.isPattern = is_pattern

    field: str
    isPattern: bool


def equals(source: str, change_to: str) -> bool:
    if source == change_to:
        return True
    else:
        return False


def matches(source: str, change_to: str) -> bool:
    return re.fullmatch(change_to, source) is not None


def index_source(source: List[str]) -> List[Tuple[str, int]]:
    indexed_source: List[Tuple[str, int]] = []
    for index in range(len(source)):
        indexed_source.append((source[index], index))
    return indexed_source


def take_out_garbage(indexed_source: List[Tuple[str, int]], garbage: List[Tuple[str, int]]):
    for item in garbage:
        indexed_source.remove(item)
    garbage.clear()


def sort_fields(source: List[str], change_to: List[SortItem], alphabetical: bool = False) -> List[Translation]:
    translations: List[Translation] = []

    garbage: List[Tuple[str, int]] = []
    indexed_source = index_source(source)
    if alphabetical:
        indexed_source.sort(key=lambda field: field[0])

    for change_to_index in range(len(change_to)):
        change_to_item = change_to[change_to_index]

        for item in indexed_source:
            is_matched = matches if change_to_item.isPattern else equals

            if is_matched(item[0], change_to_item.field):
                translations.append(Translation(item[1], len(translations), item[0]))
                garbage.append(item)

        take_out_garbage(indexed_source, garbage)

    for item in indexed_source:
        translations.append(Translation(item[1], len(translations), item[0]))

    return translations
