import GlassdoorScrapeCore.GlassdoorScrapUtilities as Ut
from typing import List
import re
import GlassdoorScrapeCore.GlassdoorScrapeReviews as Reviews

baseUrl = "https://www.glassdoor.com"
urlNotFound = "!Not found in original site."


class ScrapeResults:
    def __init__(self, company_id: str, name: str, review_link: str, review_pages: int, reviews: List[List[str]],
                 interview_link: str, interview_pages: int, interviews: List[List[str]]):
        self.GlassdoorId: str = company_id
        self.GlassdoorName: str = name
        self.GlassdoorReviewLink: str = review_link
        self.GlassdoorReviewPages: int = review_pages
        self.reviews: List[List[str]] = reviews
        self.GlassdoorInterviewLink: str = interview_link
        self.GlassdoorInterviewPages: int = interview_pages
        self.interviews: List[List[str]] = interviews


class NameSearchResults:
    def __init__(self, glassdoor_name: str, glassdoor_id: str, found: bool):
        self.GlassdoorName: str = glassdoor_name
        self.GlassdoorId: str = glassdoor_id
        self.found: bool = found
        if not found:
            self.BaseReviewUrl = urlNotFound
            self.BaseInterviewUrl = urlNotFound
        else:
            self.BaseReviewUrl: str = baseUrl + "/Reviews/-Reviews-" + glassdoor_id + \
                                      "_P{page}.htm?sort.sortType=RD&sort.ascending=false"
            self.BaseInterviewUrl: str = baseUrl + "/Interview/-Interview-Questions-" + glassdoor_id + \
                                         "_P{page}.htm?sort.sortType=RD&sort.ascending=false"


def get_gd_globals(html_string) -> str:
    return Ut.get_string_between(html_string, "window.gdGlobals", "</script>", "", True)


def parse_company_overview(html_string) -> NameSearchResults:
    gd_globals = get_gd_globals(html_string)

    company_data = Ut.get_string_between(gd_globals, "'employer'", "}", "", False)
    company_data = re.sub("'name'\s*:\s*", "'name':", company_data)
    company_data = re.sub("'id'\s*:\s*", "'id':", company_data)

    glassdoor_name = Ut.get_string_between(company_data, "'name':\"", '"', "", False)
    glassdoor_id = "E" + Ut.get_string_between(company_data, "'id':\"", '"', "", False)
    if glassdoor_id == "":
        found = False
    else:
        found = True

    return NameSearchResults(glassdoor_name, glassdoor_id, found)


def search_company_name(company: str) -> NameSearchResults:
    company = Ut.encode_url(company)
    url = baseUrl + "/Reviews/company-reviews.htm?sc.keyword=" + company
    html_string = Ut.download_string(url)
    returned_gd_globals = get_gd_globals(html_string)

    if re.search("'analyticsUrl'\s*:\s*\"/employerInfo", returned_gd_globals, re.MULTILINE) is not None:
        print("Employer info retrieved")
        return parse_company_overview(html_string)
    else:
        print("Search list retrieved, taking the first result")

        overview_url = Ut.get_string_between(html_string, "href='/Overview/", ".htm'", "", True)
        if overview_url == "":
            print("The search did not find any matching companies")
            return NameSearchResults("", "", False)

        html_string = Ut.download_string(baseUrl + "/Overview/" + overview_url + ".htm")
        print("Employer info retrieved")
        return parse_company_overview(html_string)


def get_company_data(company: str, max_pages: int = 0) -> ScrapeResults:
    if company is not None and len(company) > 0:
        search_results = search_company_name(company)

        if not search_results.found:
            return ScrapeResults(search_results.GlassdoorId, search_results.GlassdoorName, search_results.BaseReviewUrl,
                                 -1, [], search_results.BaseInterviewUrl, -1, [])
        else:
            reviews_result = Ut.scrape_list(search_results.BaseReviewUrl, Reviews.parse_html, max_pages)

            return ScrapeResults(search_results.GlassdoorId, search_results.GlassdoorName, search_results.BaseReviewUrl,
                                 reviews_result[0], reviews_result[1], search_results.BaseInterviewUrl, -1, [])
