from typing import List
from urllib.request import Request, urlopen, HTTPError
from lxml import html
from lxml.html.clean import clean_html
import time
import re


baseUrl = "https://www.glassdoor.com"

class ScrapeResults:
    def __init__(self, id: str, name: str, link: str, pages: int, reviews: List[List[str]]):
        self.GlassdoorId: str = id
        self.GlassdoorName: str = name
        self.GlassdoorLink: str = link
        self.GlassdoorPages: int = pages
        self.reviews: List[List[str]] = reviews

class NameSearchResults:
    def __init__(self, GlassdoorName: str, GlassdoorId: str, found: bool):
        self.GlassdoorName: str = GlassdoorName
        self.GlassdoorId: str = GlassdoorId
        self.found: bool = found
        self.BaseUrl: str = baseUrl + "/Reviews/-Reviews-" + GlassdoorId + "_P{page}.htm?sort.sortType=RD&sort.ascending=false"

def _DownloadString(URL):
    html = ""
    while html == "":
            try:
                print("Download string from "+URL)
                q = Request(URL)
                q.add_header('User-Agent', 'Mozilla/5.0')
                charset = 'utf-8'
                resource = urlopen(q)
                try:
                    html = resource.read().decode(charset)
                except:
                    charset = 'unicode'
                    html = resource.read().decode(charset)
            except HTTPError as err:
                print("Error fetching URL, To retry after 15 seconds. ERROR CODE: " + err.code)
                if err.code == 404:
                    return None
                _PauseScript(15)
    return html


# Pauses script execution
def _PauseScript(SecondsPause):
    print("Sleeping for "+str(SecondsPause)+" seconds")
    time.sleep(SecondsPause)


# Returns a list of substrings found in between strings
def _GetListOfSubstrings(stringSubject, string1, string2, Limit = -1):
    MyList = []
    intstart = 0
    strlength = len(stringSubject)
    continueloop = 1

    while intstart < strlength and continueloop == 1 and len(MyList) != Limit:
        intindex1 = stringSubject.find(string1, intstart)
        if intindex1 != -1:  # The substring was found, lets proceed
            intindex1 = intindex1 + len(string1)
            intindex2 = stringSubject.find(string2, intindex1)
            if intindex2 != -1:
                subsequence = stringSubject[intindex1:intindex2]
                subsequence = subsequence.strip()
                MyList.append(subsequence)
                intstart = intindex2 + len(string2)
            else:
                continueloop = 0
        else:
            continueloop = 0
    return MyList


# Returns a string between two tags
def _GetStringBetween(stringSubject, string1, string2, ReturnStringIfNotFound ="", FormatAsHtml = True):
    MyList = _GetListOfSubstrings(stringSubject, string1, string2, 1)
    if len(MyList) == 0:
        return ReturnStringIfNotFound
    TheString = MyList[0]
    if FormatAsHtml == True:
        return _StripHtml(TheString)
    else:
        return TheString


# Strips html from a string, you need to make sure lxml is installed first
def _StripHtml(stringSubject):
    tree = html.fromstring(stringSubject)
    clean_tree = clean_html(tree)
    return clean_tree.text_content().strip()


# Encodes a string to be URL safe
def _EncodeURL(stringToEncode):
    from urllib.parse import quote
    return quote(stringToEncode)


# region ScrapeSpecificFunctions
def _DecodePageNo(PageNoString):
    try:
        number = int(PageNoString.strip())
        return number
    except:
        return 1


# BoxColor
def _DecodeBoxColor(HTMLString):
    if HTMLString.find("yellow", 0) != -1:
        return "Yellow"
    elif HTMLString.find("green", 0) != -1:
        return "Green"
    elif HTMLString.find("red", 0) != -1:
        return "Red"
    return ""


# Parses the HTML
def _ParseHTML(HTMLString) -> List[List[str]]:
    HtmlList = _GetListOfSubstrings(HTMLString, "<li class=' empReview", "</span></span></div></div></div></div></div></div></li>")
    print("Reviews to parse: " + str(len(HtmlList)))
    # Each will have a list appended
    OutputListing: List[List[str]] = []
    for mainlist in range(0, len(HtmlList)):
        row = HtmlList[mainlist]
        # Parse the current listing
        RowList: List[str] = []
        # Company Name
        _str = _GetStringBetween(HTMLString, "</script><title>", "Reviews |", "")
        RowList.append(_str)

        # ReviewDate
        _str = _GetStringBetween(row, "datetime=\"", "\">", "")
        RowList.append(_str)
        # Helpful count
        _str = _GetStringBetween(row, "<span class=\"helpfulCount subtle\">", "</span>", "")
        _str = _str.replace("Helpful", "")
        _str = _str.replace("(", "")
        _str = _str.replace(")", "")
        _str = _str.strip()
        RowList.append(_str)
        # Title (of the review)
        _str = _GetStringBetween(row, "<span class=\"summary \">", "</span>", "")
        _str = _str.strip("\"")
        RowList.append(_str)
        # Rating of Review
        _str = _GetStringBetween(row, "<span class=\"rating\"><span class=\"value-title\" title=\"", "></span>", "")
        _str = _str.strip("\"")
        RowList.append(_str)
        # Current Employee / Past
        _str = _GetStringBetween(row, "<span class='authorJobTitle middle reviewer'>", "</span>", "")
        _str = _str.strip()
        _current = _str
        _current = _GetStringBetween((">" + _current), ">", "Employee", "")
        RowList.append(_current)

        # Employee title
        _current = _str
        _current = _GetStringBetween(_current + "</", "-", "</", "")
        RowList.append(_current)

        # Employee type
        _str = _GetStringBetween(row, "<p class=' tightBot mainText'>", "</p>", "")
        if _str.find("full", 0) != -1:
            RowList.append("Full time")
        elif _str.find("half", 0) != -1:
            RowList.append("Half time")
        else:
            RowList.append(_str)

        # Location
        _str = _GetStringBetween(row, "<span class='authorLocation middle'>", "></span>", "")
        RowList.append(_str)

        # Recommends
        _str = _GetStringBetween(row, "<i class", "Recommends</span>", "", False)
        _str = _DecodeBoxColor(_str)
        RowList.append(_str)

        # Outlook
        _str = _GetStringBetween(row, "</i></div><div class=\"cell\"><span class='middle'>", "Outlook</span>", "")
        if _str.find("Positive", 0) != -1:
            RowList.append("Positive")
        elif _str.find("Negative", 0) != -1:
            RowList.append("Negative")
        elif _str.find("Neutral", 0) != -1:
            RowList.append("Neutral")
        else:
            RowList.append(_str)

        # CEO
        _str = _GetStringBetween(row, "<i class", "CEO</span>", "", False)
        _str = _DecodeBoxColor(_str)
        RowList.append(_str)

        # Time Employed:
        _str = _GetStringBetween(row, "<p class=' tightBot mainText'>", "</p>", "")
        if _str.find("More than a year", 0) != -1:
            RowList.append("More than a year")
        elif _str.find("Less than a year", 0) != -1:
            RowList.append("Less than a year")
        else:
            RowList.append(_str)

        # Pros
        _str = _GetStringBetween(row, "<p class=' pros mainText truncateThis wrapToggleStr'>", "</p>", "")
        RowList.append(_str)

        # Cons
        _str = _GetStringBetween(row, "<p class=' cons mainText truncateThis wrapToggleStr'>", "</p>", "")
        RowList.append(_str)

        # Advice to management
        _str = _GetStringBetween(row, "<p class=' adviceMgmt mainText truncateThis wrapToggleStr'>", "</p>", "")
        RowList.append(_str)

        # append the list
        OutputListing.append(RowList)

    return OutputListing


def _getGdGlobals(HTML) -> str:
    return _GetStringBetween(HTML, "window.gdGlobals", "</script>", "", True)


def _parseCompanyOverview(HTML) -> NameSearchResults:
    gdGlobals = _getGdGlobals(HTML)

    companyData = _GetStringBetween(gdGlobals, "'employer'", "}", "", False)
    companyData = re.sub("'name'\s*:\s*", "'name':", companyData)
    companyData = re.sub("'id'\s*:\s*", "'id':", companyData)

    GlassdoorName = _GetStringBetween(companyData, "'name':\"", '"', "", False)
    GlassdoorId = "E" + _GetStringBetween(companyData, "'id':\"", '"', "", False)
    if GlassdoorId == "":
        found = False
    else:
        found = True

    return NameSearchResults(GlassdoorName, GlassdoorId, found)


def searchCompanyName(company: str) -> NameSearchResults:
    company = _EncodeURL(company)

    URL = baseUrl + "/Reviews/company-reviews.htm?sc.keyword=" + company

    HTML = _DownloadString(URL)
    returnedGdGlobals = _getGdGlobals(HTML)

    if re.search("'analyticsUrl'\s*:\s*\"/employerInfo", returnedGdGlobals, re.MULTILINE) is not None:
        print("Employer info retrieved")
        return _parseCompanyOverview(HTML)
    else:
        print("Search list retrieved, taking the first result")

        overviewUrl = _GetStringBetween(HTML, "href='/Overview/", ".htm'", "", True)
        if overviewUrl == "":
            print("The search did not find any matching companies")
            return NameSearchResults("", "", False)

        HTML = _DownloadString(baseUrl + "/Overview/" + overviewUrl + ".htm")
        print("Employer info retrieved")
        return _parseCompanyOverview(HTML)


def getReviews(company: str, maxPages: int = 0) -> ScrapeResults:
    GlassdoorId: str = ""
    GlassdoorName: str = ""
    GlassdoorLink: str = ""
    GlassdoorPages: int = 1
    reviews: List[List[str]] = []

    if company is not None and len(company) > 0:
        searchResults = searchCompanyName(company)

        if not searchResults.found:
            GlassdoorId = ""
            GlassdoorName = ""
            GlassdoorLink = "!Not found in original site."
            GlassdoorPages = -1
        else:
            GlassdoorId = searchResults.GlassdoorId
            GlassdoorName = searchResults.GlassdoorName
            GlassdoorLink = searchResults.BaseUrl

            tryScrape = True
            while tryScrape and (GlassdoorPages <= maxPages or maxPages == 0):
                currenturl = GlassdoorLink.replace("{page}", str(GlassdoorPages))

                HTML = _DownloadString(currenturl)
                if HTML is not None:
                    parsedReviews = _ParseHTML(HTML)
                    for review in parsedReviews:
                        reviews.append(review)

                    if HTML.find("<li class='next'><span class='disabled'><i><span>Next</span>", 0) != -1:
                        tryScrape = False

                    if len(parsedReviews) != 10:
                        tryScrape = False

                    GlassdoorPages = GlassdoorPages + 1
                    _PauseScript(1)  # how long between scrapes

                else:
                    tryScrape = False

            GlassdoorPages = GlassdoorPages - 1

    return ScrapeResults(GlassdoorId, GlassdoorName, GlassdoorLink, GlassdoorPages, reviews)
