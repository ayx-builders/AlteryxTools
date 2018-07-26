import GlassdoorScrapeCore.GlassdoorScrapeUtilities as Ut


def decode_experience(html_string):
    if html_string.find("Positive", 0) != -1:
        return "Positive Experience"
    elif html_string.find("Neutral", 0) != -1:
        return "Neutral Experience"
    elif html_string.find("Negative", 0) != -1:
        return "Negative Experience"
    return ""


def decode_offer(html_string):
    if html_string.find("Accepted", 0) != -1:
        return "Accepted Offer"
    elif html_string.find("Declined", 0) != -1:
        return "Declined Offer"
    elif html_string.find("No Offer", 0) != -1:
        return "No Offer"
    return ""


def decode_difficulty(html_string):
    if html_string.find("Hard", 0) != -1:
        return "Hard"
    elif html_string.find("Average", 0) != -1:
        return "Average"
    elif html_string.find("Easy", 0) != -1:
        return "Easy"
    elif html_string.find("Difficult", 0) != -1:
        return "Difficult"
    return ""


def decode_getting_interview(html_string):
    html_string = html_string.upper()
    if html_string.find(" ONLINE ", 0) != -1:
        return "Online"
    elif html_string.find("EMPLOY", 0) != -1:
        return "Employee Referral"
    elif html_string.find("RECRUITING", 0) != -1:
        return "Campus Recruiting"
    elif html_string.find("CAMPUS", 0) != -1:
        return "Campus Recruiting"
    return ""


def parse_html(html_string):
    company_name = Ut.get_string_between(html_string, "</script><title>", "Interview Questions |", "")
    print("Company Name: " + company_name)

    interview_list = Ut.get_list_of_substrings(html_string, "<li class=' empReview cf ' id='InterviewReview", "</li>")
    if len(interview_list) == 0:
        interview_list = Ut.get_list_of_substrings(html_string,
                                                   "<li class=' lockedReview empReview cf ' id='InterviewReview_",
                                                   "</li>")

    print("Interviews to parse: " + str(len(interview_list)))
    # Each will have a list appended
    output_listing = []
    for main_list in range(0, len(interview_list)):
        row = interview_list[main_list]
        # Parse the current listing
        row_list = []
        # Company Name
        _str = company_name
        row_list.append(_str)

        # Interview Date
        _str = Ut.get_string_between(row, "datetime=\"", "\">", "")
        row_list.append(_str)

        # Title (Analyst Interview)
        _str = Ut.get_string_between(row, "<span class='reviewer'>", "</span>", "")
        _str = _str.strip()
        row_list.append(_str)

        # Experience
        experience = Ut.get_string_between(row, "<div class='flex-grid'>",
                                           "<p class=\"strong margTopMd tightBot\">Application</p>", "")
        experience = experience.strip()
        if len(experience) == 0:
            experience = Ut.get_string_between(row, "<div class='flex-grid'>",
                                               "<p class=\"strong margTopMd tightBot\">Interview</p>", "")

        _str = decode_experience(experience)
        row_list.append(_str)

        # Offer
        _str = decode_offer(experience)
        row_list.append(_str)

        # Difficulty
        _str = decode_difficulty(experience)
        row_list.append(_str)

        # GettingInterview
        _Application = Ut.get_string_between(row,
                                             "<p class='applicationDetails mainText truncateThis wrapToggleStr '>",
                                             "</p>", "")
        _current = decode_getting_interview(_Application)
        row_list.append(_current)

        # Application
        row_list.append(_Application)

        # Interview (description/verbatim)
        _str = Ut.get_string_between(row,
                                     "<p class='interviewDetails mainText truncateThis wrapToggleStr '>",
                                     "</p>", "")
        row_list.append(_str)

        # Interview (Questions)
        _str = Ut.get_string_between(row,
                                     "<span class='interviewQuestion noPadVert truncateThis wrapToggleStr ' data-truncate-words='70'>",
                                     "class", "", True)
        row_list.append(_str)

        # append the list
        output_listing.append(row_list)

    return output_listing
