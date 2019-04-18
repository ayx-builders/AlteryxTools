# There MUST be a .env file with JIRA_SERVER, JIRA_USERNAME and JIRA_PASSWORD settings in this directory for the jira tests to work

import unittest
import os
from dotenv import load_dotenv

import JiraPyCore as Core


class MyTestCase(unittest.TestCase):
    load_dotenv()

    def test_GetProjects(self):
        projects = Core.retrieve_projects(server(), username(), password())
        self.assertNotEqual(0, len(projects))

    def test_GetIssuesNoFilter(self):
        issues = Core.retrieve_issues(server(), username(), password(), max_issues=10)
        self.assertNotEqual(0, len(issues))

    def test_GetIssuesFiltered(self):
        issues = Core.retrieve_issues(server(), username(), password(),
                                      jql="assignee = currentUser() AND resolution = Unresolved", max_issues=10)
        self.assertNotEqual(0, len(issues))

    def test_GetIssueSprints(self):
        issue_sprints = Core.retrieve_issue_sprints(server(), username(), password(), max_issues=100)
        self.assertNotEqual(0, len(issue_sprints))

    def test_DeserializeSprint(self):
        sprint = 'com.atlassian.greenhopper.service.sprint.Sprint@1286f4a8[id=1,rapidViewId=1,state=ACTIVE,name=Hello World,startDate=2019-04-08T07:00:00.000+02:00,endDate=2019-04-22T07:00:00.000+02:00,completeDate=<null>,sequence=128,goal=]'
        issue_sprint: Core.IssueSprint = Core._parse_issue_sprint("key", sprint)
        self.assertEqual('Hello World', issue_sprint.Sprint_Name)
        self.assertEqual('ACTIVE', issue_sprint.Sprint_State)
        self.assertEqual('', issue_sprint.Sprint_Goal)
        self.assertEqual('2019-04-08T07:00:00.000+02:00', issue_sprint.Sprint_Start)
        self.assertEqual('2019-04-22T07:00:00.000+02:00', issue_sprint.Sprint_End)
        self.assertEqual('<null>', issue_sprint.Sprint_Completed)

    def test_GetIssueComponents(self):
        issues = Core.retrieve_issue_components(server(), username(), password(), max_issues=10)
        self.assertNotEqual(0, len(issues))

    def test_GetComments(self):
        issues = Core.retrieve_comments(server(), username(), password(), max_issues=10, jql="comment !~ '@'")
        self.assertNotEqual(0, len(issues))

    def test_GetIssueCommentsWithoutComments(self):
        issues = Core.retrieve_comments(server(), username(), password(), max_issues=10, jql="comment ~ 'Hello world'")
        self.assertEqual(0, len(issues))


if __name__ == '__main__':
    unittest.main()


def server() -> str:
    return os.getenv("JIRA_SERVER")


def username() -> str:
    return os.getenv("JIRA_USERNAME")


def password() -> str:
    return os.getenv("JIRA_PASSWORD")
