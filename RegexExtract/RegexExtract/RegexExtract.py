import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import re


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.DataFieldName: str = None
        self.Pattern: str = None
        self.MatchFieldName: str = None
        self.input: IncomingInterface = None
        self.MatchOutput: Sdk.OutputAnchor = None
        self.NoMatchOutput: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.DataFieldName = Et.fromstring(str_xml).find('DataField').text if 'DataField' in str_xml else None
        self.Pattern = Et.fromstring(str_xml).find('Pattern').text if 'Pattern' in str_xml else None
        self.MatchFieldName = Et.fromstring(str_xml).find('ExtractedMatchField').text if 'ExtractedMatchField' in str_xml else None

        # Validity checks.
        if self.DataFieldName is None:
            self.display_error_msg('Text field cannot be empty.')

        if self.Pattern is None:
            self.display_error_msg('Pattern cannot be empty.')

        if self.MatchFieldName is None:
            self.display_error_msg('Field name cannot be empty.')
        elif len(self.MatchFieldName) > 255:
            self.display_error_msg('Field name cannot be greater than 255 characters.')

        # Getting the output anchor from Config.xml by the output connection name
        self.MatchOutput = self.output_anchor_mgr.get_output_anchor('Matches')
        self.NoMatchOutput = self.output_anchor_mgr.get_output_anchor('NoMatches')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        self.MatchOutput.assert_close()
        self.NoMatchOutput.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.record_copier: Sdk.RecordCopier = None
        self.record_creator: Sdk.RecordCreator = None
        self.MatchField: Sdk.Field = None
        self.DataField: Sdk.Field = None

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Make sure the user provided a field to parse
        if self.parent.DataFieldName is None:
            self.parent.display_error_msg('Select a field')
            return False

        # Get information about the field we will be parsing
        self.DataField = record_info_in.get_field_by_name(self.parent.DataFieldName)
        match_field_type: Sdk.FieldType = self.DataField.type
        match_field_size: int = self.DataField.size

        # Returns a new, empty RecordCreator object that is identical to record_info_in.
        record_info_out = record_info_in.clone()

        # Adds field to record with specified name and output type.
        self.MatchField = record_info_out.add_field(self.parent.MatchFieldName, match_field_type, match_field_size)

        # Lets the downstream tools know what the outgoing record metadata will look like
        self.parent.MatchOutput.init(record_info_out)
        self.parent.NoMatchOutput.init(record_info_in)

        # Creating a new, empty record creator based on record_info_out's record layout.
        self.record_creator = record_info_out.construct_record_creator()

        # Instantiate a new instance of the RecordCopier class.
        self.record_copier = Sdk.RecordCopier(record_info_out, record_info_in)

        # Map each column of the input to where we want in the output.
        for index in range(record_info_in.num_fields):
            # Adding a field index mapping.
            self.record_copier.add(index, index)

        # Let record copier know that all field mappings have been added.
        self.record_copier.done_adding()

        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        # Copy the data from the incoming record into the outgoing record.
        self.record_creator.reset()
        self.record_copier.copy(self.record_creator, in_record)

        # Get the text to parse and set the matches counter
        data: str = self.DataField.get_as_string(in_record)
        matches: int = 0

        # Iterate through the matches and output to the Match output anchor
        for match in re.finditer("(%s)" % self.parent.Pattern, data):
            matched_str: str = match.group(1)
            self.MatchField.set_from_string(self.record_creator, matched_str)
            out_record = self.record_creator.finalize_record()
            self.parent.MatchOutput.push_record(out_record)
            matches = matches + 1

        # If no matches were found, output to the No Matches output anchor
        if matches == 0:
            self.parent.NoMatchOutput.push_record(in_record)

        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.MatchOutput.update_progress(d_percent)
        self.parent.NoMatchOutput.update_progress(d_percent)

    def ii_close(self):
        # Close outgoing connections.
        self.parent.MatchOutput.close()
        self.parent.NoMatchOutput.close()
