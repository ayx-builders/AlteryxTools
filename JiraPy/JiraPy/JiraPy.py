import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import JiraPyCore as Core
from typing import List


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr
        self.Label = "JiraPy (" + str(self.n_tool_id) + ")"

        # Custom properties
        self.Server: str = None
        self.Username: str = None
        self.Password: str = None
        self.ObjectType: str = None
        self.Filter: str = None
        self.MaxIssues: int = None
        self.Output: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.Server = Et.fromstring(str_xml).find('Server').text if 'Server' in str_xml else None
        self.Username = Et.fromstring(str_xml).find('Username').text if 'Username' in str_xml else None
        self.Password = Et.fromstring(str_xml).find('Password').text if 'Password' in str_xml else None
        self.ObjectType = Et.fromstring(str_xml).find('ObjectType').text if 'ObjectType' in str_xml else None
        self.Filter = Et.fromstring(str_xml).find('Filter').text if 'Filter' in str_xml else None
        self.MaxIssues = int(Et.fromstring(str_xml).find("MaxIssues").text) if 'MaxIssues' in str_xml else 0
        if self.MaxIssues == 0: self.MaxIssues = None

        # Validity checks.
        if self.Server is None:
            self.display_error_msg('A server address must be entered.')
        if self.ObjectType is None:
            self.display_error_msg('An object type must be selected.')

        # Getting the output anchor from Config.xml by the output connection name
        self.Output = self.output_anchor_mgr.get_output_anchor('Output')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        return None

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self._send_progress(0, 0)
        update_only = self.alteryx_engine.get_init_var(self.n_tool_id, 'UpdateOnly') == 'True'
        result = False
        if   self.ObjectType == 'Projects'        : result = self._import_projects(update_only)
        elif self.ObjectType == 'Issues'          : result = self._import_issues(update_only)
        elif self.ObjectType == 'Issue Sprints'   : result = self._import_issue_sprints(update_only)
        elif self.ObjectType == 'Issue Components': result = self._import_issue_components(update_only)
        elif self.ObjectType == 'Comments'        : result = self._import_comments(update_only)
        self.Output.close()
        return result

    def pi_close(self, b_has_errors: bool):
        self.Output.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)

    def _import_projects(self, update_only: bool) -> bool:
        record_info = self._get_project_record_info()
        get_data = lambda: Core.retrieve_projects(self.Server, self.Username, self._decrypt_password())
        return self._push_data(record_info, update_only, get_data)

    def _import_issues(self, update_only: bool) -> bool:
        record_info = self._get_issue_record_info()
        self.Output.init(record_info)
        if update_only:
            return False

        records = Core.retrieve_issues(self.Server, self.Username, self._decrypt_password(), self.Filter, self.MaxIssues)
        creator: Sdk.RecordCreator = record_info.construct_record_creator()
        processed = 0
        for record in records:
            self._set_field(creator, record_info.get_field_by_name('Key'), record.Key)
            self._set_field(creator, record_info.get_field_by_name('Assignee_Name'), record.Assignee_Name)
            self._set_field(creator, record_info.get_field_by_name('Assignee_DisplayName'), record.Assignee_DisplayName)
            self._set_field(creator, record_info.get_field_by_name('Created'), record.Created)
            self._set_field(creator, record_info.get_field_by_name('Creator_Name'), record.Creator_Name)
            self._set_field(creator, record_info.get_field_by_name('Creator_DisplayName'), record.Creator_DisplayName)
            self._set_field(creator, record_info.get_field_by_name('Description'), record.Description)
            self._set_field(creator, record_info.get_field_by_name('Issue_Type'), record.Issue_Type)
            self._set_field(creator, record_info.get_field_by_name('Priority'), record.Priority)
            self._set_field(creator, record_info.get_field_by_name('Project_Key'), record.Project_Key)
            self._set_field(creator, record_info.get_field_by_name('Project_Name'), record.Project_Name)
            self._set_field(creator, record_info.get_field_by_name('Reporter_Name'), record.Reporter_Name)
            self._set_field(creator, record_info.get_field_by_name('Reporter_DisplayName'), record.Reporter_DisplayName)
            self._set_field(creator, record_info.get_field_by_name('Resolution'), record.Resolution)
            self._set_field(creator, record_info.get_field_by_name('Resolution_Date'), record.Resolution_Date)
            self._set_field(creator, record_info.get_field_by_name('Status'), record.Status)
            self._set_field(creator, record_info.get_field_by_name('Summary'), record.Summary)
            for custom_field, value in record.Custom_Fields.items():
                self._set_field(creator, record_info.get_field_by_name(custom_field), value)

            output = creator.finalize_record()
            self.Output.push_record(output)
            creator.reset()
            processed += 1
            self._send_progress(processed, processed / len(records))
        return True

    def _import_issue_sprints(self, update_only: bool) -> bool:
        record_info = self._get_issue_sprint_record_info()
        get_data = lambda: Core.retrieve_issue_sprints(self.Server, self.Username, self._decrypt_password(),
                                                       self.Filter, self.MaxIssues)
        return self._push_data(record_info, update_only, get_data)

    def _import_issue_components(self, update_only: bool) -> bool:
        record_info = self._get_issue_component_record_info()
        get_data = lambda: Core.retrieve_issue_components(self.Server, self.Username, self._decrypt_password(),
                                                          self.Filter, self.MaxIssues)
        return self._push_data(record_info, update_only, get_data)

    def _import_comments(self, update_only: bool) -> bool:
        record_info = self._get_issue_comment_record_info()
        get_data = lambda: Core.retrieve_comments(self.Server, self.Username, self._decrypt_password(),
                                                  self.Filter, self.MaxIssues)
        return self._push_data(record_info, update_only, get_data)

    def _push_data(self, record_info: Sdk.RecordInfo, update_only: bool, get_data_callback) -> bool:
        self.Output.init(record_info)
        if update_only:
            return False

        records = get_data_callback()
        creator: Sdk.RecordCreator = record_info.construct_record_creator()
        processed = 0
        for record in records:
            for field in record_info:
                self._set_field(creator, field, record.__getattribute__(field.name))

            output = creator.finalize_record()
            self.Output.push_record(output)
            creator.reset()
            processed += 1
            self._send_progress(processed, processed / len(records))
        return True

    def _send_progress(self, processed: int, percent: float):
        self.Output.output_record_count(processed)
        self.Output.update_progress(percent)
        self.alteryx_engine.output_tool_progress(self.n_tool_id, percent)

    def _get_project_record_info(self) -> Sdk.RecordInfo:
        return self._generate_record_info([
            'Project_Key',
            'Project_Name',
            'Project_Type',
        ])

    def _get_issue_record_info(self) -> Sdk.RecordInfo:
        custom_fields: List[str] = Core.retrieve_single_value_custom_fields(self.Server, self.Username,
                                                                            self._decrypt_password())
        standard_fields: List[str] = [
            'Key',
            'Assignee_Name',
            'Assignee_DisplayName',
            'Created',
            'Creator_Name',
            'Creator_DisplayName',
            'Description',
            'Issue_Type',
            'Priority',
            'Project_Key',
            'Project_Name',
            'Reporter_Name',
            'Reporter_DisplayName',
            'Resolution',
            'Resolution_Date',
            'Status',
            'Summary',
        ]
        return self._generate_record_info(standard_fields + custom_fields)

    def _get_issue_sprint_record_info(self) -> Sdk.RecordInfo:
        return self._generate_record_info([
            'Issue_Key',
            'Sprint_Name',
            'Sprint_Goal',
            'Sprint_State',
            'Sprint_Start',
            'Sprint_End',
            'Sprint_Completed',
        ])

    def _get_issue_component_record_info(self) -> Sdk.RecordInfo:
        return self._generate_record_info([
            'Issue_Key',
            'Component_Name',
            'Component_Description',
        ])

    def _get_issue_comment_record_info(self) -> Sdk.RecordInfo:
        return self._generate_record_info([
            'Issue_Key',
            'Comment_Author_Name',
            'Comment_Author_DisplayName',
            'Comment_Body',
            'Comment_Created',
            'Comment_Update_Author_Name',
            'Comment_Update_Author_DisplayName',
            'Comment_Updated',
        ])

    def _decrypt_password(self) -> str:
        return self.alteryx_engine.decrypt_password(self.Password)

    @staticmethod
    def _set_field(creator: Sdk.RecordCreator, field: Sdk.Field, value: str):
        if value is None:
            field.set_null(creator)
        else:
            field.set_from_string(creator, value)

    def _generate_record_info(self, field_names: List[str]) -> Sdk.RecordInfo:
        record_info: Sdk.RecordInfo = Sdk.RecordInfo(self.alteryx_engine)
        for field_name in field_names:
            record_info.add_field(field_name, Sdk.FieldType.v_wstring, 1073741823, 0, self.Label)
        return record_info
