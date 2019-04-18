import re
from typing import List, Dict
from jira import JIRA


class Project:
    def __init__(self, project_key: str, project_name: str, project_type: str):
        self.Project_Key: str = project_key
        self.Project_Name: str = project_name
        self.Project_Type: str = project_type


class Issue:
    def __init__(self, key: str, assignee_name: str, assignee_displayname: str, created: str,
                 creator_name: str, creator_displayname: str, description: str, issue_type: str, priority: str,
                 project_key: str, project_name: str, reporter_name: str, reporter_displayname: str, resolution: str,
                 resolution_date: str, status: str, summary: str, custom_fields: Dict[str, str]):
        self.Key = key
        self.Assignee_Name: str = assignee_name
        self.Assignee_DisplayName: str = assignee_displayname
        self.Created: str = created
        self.Creator_Name: str = creator_name
        self.Creator_DisplayName: str = creator_displayname
        self.Description: str = description
        self.Issue_Type: str = issue_type
        self.Priority: str = priority
        self.Project_Key: str = project_key
        self.Project_Name: str = project_name
        self.Reporter_Name: str = reporter_name
        self.Reporter_DisplayName: str = reporter_displayname
        self.Resolution: str = resolution
        self.Resolution_Date: str = resolution_date
        self.Status: str = status
        self.Summary: str = summary
        self.Custom_Fields: Dict[str, str] = custom_fields


class IssueSprint:
    def __init__(self, issue_key: str, sprint_name: str, sprint_goal: str, sprint_state: str, sprint_start: str,
                 sprint_end: str, sprint_completed: str):
        self.Issue_Key: str = issue_key
        self.Sprint_Name: str = sprint_name
        self.Sprint_Goal: str = sprint_goal
        self.Sprint_State: str = sprint_state
        self.Sprint_Start: str = sprint_start
        self.Sprint_End: str = sprint_end
        self.Sprint_Completed: str = sprint_completed


class IssueComponent:
    def __init__(self, issue_key: str, component_name: str, component_description: str):
        self.Issue_Key: str = issue_key
        self.Component_Name: str = component_name
        self.Component_Description: str = component_description


class IssueComment:
    def __init__(self, issue_key: str, comment_author_name: str, comment_author_displayname: str, comment_body: str,
                 comment_created: str, comment_update_author_name: str, comment_update_author_displayname: str,
                 comment_updated: str):
        self.Issue_Key: str = issue_key
        self.Comment_Author_Name: str = comment_author_name
        self.Comment_Author_DisplayName: str = comment_author_displayname
        self.Comment_Body: str = comment_body
        self.Comment_Created: str = comment_created
        self.Comment_Update_Author_Name: str = comment_update_author_name
        self.Comment_Update_Author_DisplayName: str = comment_update_author_displayname
        self.Comment_Updated: str = comment_updated


def retrieve_single_value_custom_fields(server: str, username: str, password: str) -> List[str]:
    jira = _get_jira(server, username, password)
    jira_fields = _exclude_array_fields(_get_system_custom_fields(jira))
    fields: List[str] = []
    for jira_field in jira_fields:
        fields.append(_generate_custom_field_name(jira_field))
    return fields


def retrieve_projects(server: str, username: str, password: str) -> List[Project]:
    jira = _get_jira(server, username, password)
    returned_projects = jira.projects()
    jira.close()

    projects: List[Project] = []
    for returned_project in returned_projects:
        projects.append(Project(
            project_key=returned_project.key,
            project_name=returned_project.name,
            project_type=returned_project.projectTypeKey
        ))
    return projects


def retrieve_issues(server: str, username: str, password: str, jql: str = '', max_issues: int = None) -> List[Issue]:
    jira = _get_jira(server, username, password)
    returned_issues = jira.search_issues(jql_str=jql, maxResults=max_issues)
    system_custom_fields = _get_system_custom_fields(jira)
    jira.close()

    issues: List[Issue] = []
    for returned_issue in returned_issues:
        issue_custom_fields: Dict[str, str] = _get_issue_custom_fields(system_custom_fields, returned_issue)

        issues.append(Issue(
            key=returned_issue.key,
            assignee_name=_get_name(returned_issue.fields.assignee),
            assignee_displayname=_get_display_name(returned_issue.fields.assignee),
            created=returned_issue.fields.created,
            creator_name=_get_name(returned_issue.fields.creator),
            creator_displayname=_get_display_name(returned_issue.fields.creator),
            description=returned_issue.fields.description,
            issue_type=_get_name(returned_issue.fields.issuetype),
            priority=_get_name(returned_issue.fields.priority),
            project_key=_get_key(returned_issue.fields.project),
            project_name=_get_name(returned_issue.fields.project),
            reporter_name=_get_name(returned_issue.fields.reporter),
            reporter_displayname=_get_display_name(returned_issue.fields.reporter),
            resolution=_get_name(returned_issue.fields.resolution),
            resolution_date=returned_issue.fields.resolutiondate,
            status=_get_name(returned_issue.fields.status),
            summary=returned_issue.fields.summary,
            custom_fields=issue_custom_fields,
        ))
    return issues


def retrieve_issue_sprints(server: str, username: str, password: str, jql: str = '',
                           max_issues: int = None) -> List[IssueSprint]:
    jira = _get_jira(server, username, password)
    system_custom_fields = _get_system_custom_fields(jira)
    sprint_field = None
    issue_sprints: List[IssueSprint] = []
    for field in system_custom_fields:
        if 'Sprint' == field['name']:
            sprint_field = field['id']
            break

    if sprint_field is None:
        jira.close()
        return issue_sprints

    returned_issues = jira.search_issues(jql_str=jql, maxResults=max_issues, fields=sprint_field)
    jira.close()

    for returned_issue in returned_issues:
        sprints = getattr(returned_issue.fields, sprint_field)
        if sprints is None:
            continue
        for sprint in sprints:
            issue_sprints.append(_parse_issue_sprint(returned_issue.key, sprint))

    return issue_sprints


def retrieve_issue_components(server: str, username: str, password: str, jql: str = '',
                              max_issues: int = None) -> List[IssueComponent]:
    jira = _get_jira(server, username, password)
    returned_issues = jira.search_issues(jql_str=jql, maxResults=max_issues, fields='components')
    jira.close()

    issue_components: List[IssueComponent] = []
    for returned_issue in returned_issues:
        if returned_issue.fields.components is None:
            continue
        for component in returned_issue.fields.components:
            description: str = None
            if hasattr(component, 'description'):
                description = component.description
            issue_components.append(IssueComponent(
                issue_key=returned_issue.key,
                component_name=component.name,
                component_description=description
            ))

    return issue_components


def retrieve_comments(server: str, username: str, password: str, jql: str = '',
                      max_issues: int = None) -> List[IssueComment]:
    jira = _get_jira(server, username, password)
    returned_issues = jira.search_issues(jql_str=jql, maxResults=max_issues, fields="comment")
    jira.close()

    issue_comments: List[IssueComment] = []
    for returned_issue in returned_issues:
        if returned_issue.fields.comment.comments is None:
            continue
        for comment in returned_issue.fields.comment.comments:
            issue_comments.append(IssueComment(
                issue_key=returned_issue.key,
                comment_author_name=_get_name(comment.author),
                comment_author_displayname=_get_display_name(comment.author),
                comment_body=comment.body,
                comment_created=comment.created,
                comment_update_author_name=_get_name(comment.updateAuthor),
                comment_update_author_displayname=_get_display_name(comment.updateAuthor),
                comment_updated=comment.updated
            ))

    return issue_comments


def _parse_issue_sprint(issue_key: str, serialized_sprint: str) -> IssueSprint:
    state = _extract_sprint_property(serialized_sprint, "state=", ",name=")
    name = _extract_sprint_property(serialized_sprint, "name=", ",startDate=")
    goal = _extract_sprint_property(serialized_sprint, "goal=", "]")
    start = _extract_sprint_property(serialized_sprint, "startDate=", ",endDate=")
    end = _extract_sprint_property(serialized_sprint, "endDate=", ",completeDate=")
    completed = _extract_sprint_property(serialized_sprint, "completeDate=", ",sequence=")

    return IssueSprint(
        issue_key=issue_key,
        sprint_name=name,
        sprint_state=state,
        sprint_goal=goal,
        sprint_start=start,
        sprint_end=end,
        sprint_completed=completed,
    )


def _extract_sprint_property(serialized_sprint: str, property_start: str, property_end: str) -> str:
    expression = re.compile(re.escape(property_start) + "(.*)" + re.escape(property_end))
    matches = expression.findall(serialized_sprint)
    if len(matches) > 0:
        return matches[0]
    else:
        return None


def _get_issue_custom_fields(system_custom_fields: List, issue) -> Dict[str, str]:
    issue_custom_fields: Dict[str, str] = {}
    non_array_fields = _exclude_array_fields(system_custom_fields)

    for system_field in non_array_fields:
        if system_field['schema']['type'] == 'array':
            continue
        custom_field_name: str = _generate_custom_field_name(system_field)
        custom_field_value = None
        for issue_custom_field in issue.fields.__dict__.items():
            if issue_custom_field[0] == system_field['id']:
                custom_field_value = str(issue_custom_field[1])
                break
        issue_custom_fields[custom_field_name] = custom_field_value

    return issue_custom_fields


def _generate_custom_field_name(field) -> str:
    custom_id: str = field['id'][-5:]
    custom_field_name: str = field['name'] + ' (' + custom_id + ')'
    return custom_field_name


def _get_system_custom_fields(jira: JIRA) -> List:
    system_custom_fields = []
    jira_fields = jira.fields()
    for system_field in jira_fields:
        if system_field['custom']:
            system_custom_fields.append(system_field)
    return system_custom_fields


def _exclude_array_fields(fields: List) -> List:
    non_array_fields = []
    for field in fields:
        if field['schema']['type'] != 'array':
            non_array_fields.append(field)
    return non_array_fields


def _get_jira(server: str, username: str, password: str) -> JIRA:
    return JIRA(server=server, basic_auth=(username, password), max_retries=1)


def _get_name(field) -> str:
    if field is not None:
        return field.name
    else:
        return ''


def _get_key(field) -> str:
    if field is not None:
        return field.key
    else:
        return ''


def _get_display_name(field) -> str:
    if field is not None:
        return field.displayName
    else:
        return ''
