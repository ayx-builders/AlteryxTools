import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.TextLabel: str = None
        self.TextValue: str = None
        self.input: IncomingInterface = None
        self.Details: Sdk.OutputAnchor = None
        self.Count: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.TextLabel = Et.fromstring(str_xml).find('TextLabel').text if 'TextLabel' in str_xml else None
        self.TextValue = Et.fromstring(str_xml).find('TextValue').text if 'TextValue' in str_xml else None

        if self.TextLabel is None:
            self.display_error_msg("Enter a name for the output fields")

        if self.TextValue is None:
            self.display_error_msg("Enter a label describing the output")

        # Getting the output anchor from Config.xml by the output connection name
        self.Details = self.output_anchor_mgr.get_output_anchor('Details')
        self.Count = self.output_anchor_mgr.get_output_anchor('Count')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        self.Count.assert_close()
        self.Details.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent
        self.records: int = 0

        # Custom properties
        source = "Record Count Reporter (" + str(self.parent.n_tool_id) + ")"
        self.CountRecord = Sdk.RecordInfo(self.parent.alteryx_engine)
        self.IdField: Sdk.Field = self.CountRecord.add_field("Id", Sdk.FieldType.int16, 0, 0, source, '')
        self.LabelField: Sdk.Field = self.CountRecord.add_field(self.parent.TextLabel, Sdk.FieldType.v_wstring, 256, 0,
                                                                source, '')
        self.CountField: Sdk.Field = self.CountRecord.add_field(self.parent.TextLabel + "_Count", Sdk.FieldType.int64, 0, 0,
                                                                source, '')
        self.CountCreator: Sdk.RecordCreator = self.CountRecord.construct_record_creator()

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Make sure the user provided a field to parse
        if self.parent.TextLabel is None:
            self.parent.display_error_msg('Enter a name for the output fields')
            return False

        if self.parent.TextValue is None:
            self.parent.display_error_msg("Enter a label describing the output")
            return False

        self.parent.Details.init(record_info_in)
        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        self.records = self.records + 1
        self.parent.Details.push_record(in_record)
        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.Count.update_progress(0)
        self.parent.Details.update_progress(d_percent)

    def ii_close(self):
        self.parent.Details.close()

        self.parent.Count.init(self.CountRecord)
        self.CountCreator.reset()
        self.IdField.set_from_int32(self.CountCreator, 1)
        self.LabelField.set_from_string(self.CountCreator, self.parent.TextValue)
        self.CountField.set_from_int64(self.CountCreator, self.records)
        output = self.CountCreator.finalize_record()
        self.parent.Count.push_record(output)
        self.parent.Count.update_progress(1.0)

        self.parent.Count.close()
