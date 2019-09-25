from urllib.request import Request, urlopen, HTTPError
from lxml import html
from lxml.html.clean import clean_html
import time
from typing import List


def scrape_list(base_url: str, parse, max_pages: int) -> (int, List[List[str]]):
    pages: int = 1
    items: List[List[str]] = []

    try_scrape = True
    while try_scrape and (pages <= max_pages or max_pages == 0):
        current_url = base_url.replace("{page}", str(pages))

        html_string = download_string(current_url)
        
        if html_string is not None:
            try:
                parsed_items = parse(html_string)
            except:
                break

            for item in parsed_items:
                items.append(item)

            if html_string.find("<li class='next'><span class='disabled'><i><span>Next</span>", 0) != -1:
                try_scrape = False

            if len(parsed_items) != 10:
                try_scrape = False

            pages = pages + 1
            pause_script(1)  # how long between scrapes

        else:
            try_scrape = False

    pages = pages - 1
    return pages, items


# Pauses script execution
def pause_script(seconds_pause):
    print("Sleeping for "+str(seconds_pause)+" seconds")
    time.sleep(seconds_pause)


def download_string(url):
    html_string = ""
    while html_string == "":
            try:
                print("Download string from " + url)
                q = Request(url)
                q.add_header('User-Agent', 'Mozilla/5.0')
                charset = 'utf-8'
                resource = urlopen(q)
                try:
                    html_string = resource.read().decode(charset)
                except:
                    charset = 'unicode'
                    html_string = resource.read().decode(charset)
            except HTTPError as err:
                print("Error fetching URL, To retry after 15 seconds. ERROR CODE: " + err.code)
                if err.code == 404:
                    return None
                pause_script(15)
    return html_string


# Returns a list of substrings found in between strings
def get_list_of_substrings(string_subject, string1, string2, limit=-1):
    my_list = []
    int_start = 0
    str_length = len(string_subject)
    continue_loop = 1

    while int_start < str_length and continue_loop == 1 and len(my_list) != limit:
        int_index1 = string_subject.find(string1, int_start)
        if int_index1 != -1:  # The substring was found, lets proceed
            int_index1 = int_index1 + len(string1)
            int_index2 = string_subject.find(string2, int_index1)
            if int_index2 != -1:
                subsequence = string_subject[int_index1:int_index2]
                subsequence = subsequence.strip()
                my_list.append(subsequence)
                int_start = int_index2 + len(string2)
            else:
                continue_loop = 0
        else:
            continue_loop = 0
    return my_list


# Returns a string between two tags
def get_string_between(string_subject, string1, string2, not_found_value="", format_as_html=True):
    my_list = get_list_of_substrings(string_subject, string1, string2, 1)
    if len(my_list) == 0:
        return not_found_value
    the_string = my_list[0]
    if format_as_html:
        return strip_html(the_string)
    else:
        return the_string


# Strips html from a string, you need to make sure lxml is installed first
def strip_html(string_subject):
    tree = html.fromstring(string_subject)
    clean_tree = clean_html(tree)
    return clean_tree.text_content().strip()


# Encodes a string to be URL safe
def encode_url(string_to_encode):
    from urllib.parse import quote
    return quote(string_to_encode)


# BoxColor
def decode_box_color(html_string):
    if html_string.find("yellow", 0) != -1:
        return "Yellow"
    elif html_string.find("green", 0) != -1:
        return "Green"
    elif html_string.find("red", 0) != -1:
        return "Red"
    return ""
