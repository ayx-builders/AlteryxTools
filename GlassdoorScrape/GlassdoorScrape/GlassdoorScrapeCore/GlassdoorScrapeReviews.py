import GlassdoorScrapeCore.GlassdoorScrapeUtilities as Ut
from typing import List
import re

def parse_html(html_string) -> List[List[str]]:
    html_list = Ut.get_list_of_substrings(html_string, "<div class=\"hreview\">", "empReview")
    print("Reviews to parse: " + str(len(html_list)))
    # Each will have a list appended
    output_listing: List[List[str]] = []
    for main_list in range(0, len(html_list)):
        row = html_list[main_list]
        # Parse the current listing
        row_list: List[str] = []
        # Company Name
        _str = Ut.get_string_between(html_string, "'name':\"", '"', "")
        row_list.append(_str)

        # ReviewDate
        _str = Ut.get_string_between(row, "dateTime=\"", "\">", "")
        row_list.append(_str)
        # Helpful count
        _str = Ut.get_string_between(row, "helpfulReviews", "</div>", "")
        _str = Ut.get_string_between(_str, "(", ")", "")
        _str = re.sub("[^0-9]", "", _str)
        row_list.append(_str)
        # Title (of the review)
        _str = Ut.get_string_between(row, "<span class=\"summary\">", "</span>", "")
        _str = _str.strip("\"")
        row_list.append(_str)
        # Rating of Review
        _str = Ut.get_string_between(row, "<span class=\"rating\"><span class=\"value-title\" title=\"", "></span>", "")
        _str = _str.strip("\"")
        row_list.append(_str)
        # Current Employee / Past
        _str = Ut.get_string_between(row, "<span class=\"authorJobTitle middle reviewer\">", "</span>", "")
        _str = _str.strip()
        _current = _str
        _current = Ut.get_string_between((">" + _current), ">", "Employee", "")
        row_list.append(_current)

        # Employee title
        _current = _str
        _current = Ut.get_string_between(_current + "</", "-", "</", "")
        row_list.append(_current)

        # Employee type
        _str = Ut.get_string_between(row, "<p class=\"mainText mb-0\">", "</p>", "")
        if _str.find("full", 0) != -1:
            row_list.append("Full time")
        elif _str.find("half", 0) != -1:
            row_list.append("Half time")
        else:
            row_list.append(_str)

        # Location
        _str = Ut.get_string_between(row, "<span class=\"authorLocation\">", "></span>", "")
        row_list.append(_str)

        # Recommends
        _str = Ut.get_string_between(row, "<i class", "Recommends</span>", "", False)
        _str = Ut.decode_box_color(_str)
        row_list.append(_str)

        # Outlook
        _str = Ut.get_string_between(row, "</i></div><div class=\"cell\"><span class='middle'>", "Outlook</span>", "")
        if _str.find("Positive", 0) != -1:
            row_list.append("Positive")
        elif _str.find("Negative", 0) != -1:
            row_list.append("Negative")
        elif _str.find("Neutral", 0) != -1:
            row_list.append("Neutral")
        else:
            row_list.append(_str)

        # CEO
        _str = Ut.get_string_between(row, "<i class", "CEO</span>", "", False)
        _str = Ut.decode_box_color(_str)
        row_list.append(_str)

        # Time Employed:
        _str = Ut.get_string_between(row, "<p class=\"mainText mb-0\">", "</p>", "")
        if _str.find("More than a year", 0) != -1:
            row_list.append("More than a year")
        elif _str.find("Less than a year", 0) != -1:
            row_list.append("Less than a year")
        else:
            row_list.append(_str)

        # Pros
        _str = Ut.get_string_between(row, "<p class=\"strong\">Pros</p><p>", "</p>", "")
        row_list.append(_str)

        # Cons
        _str = Ut.get_string_between(row, "<p class=\"strong\">Cons</p><p>", "</p>", "")
        row_list.append(_str)

        # Advice to management
        _str = Ut.get_string_between(row, "<p class=\"strong\">Advice to Management</p><p>", "</p>", "")
        row_list.append(_str)

        # append the list
        output_listing.append(row_list)

    return output_listing
