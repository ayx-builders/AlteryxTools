import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import AlteryxPythonSDK as Sdk
from typing import List
from FieldSorterCore.FieldSorterCore import SortItem, sort_fields, Translation
import xml.etree.ElementTree as Et

class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.SortList: List[SortItem] = []
        self.Alphabetical: bool = False
        self.input: IncomingInterface = None
        self.output: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        sort: str = Et.fromstring(str_xml).find('SortList').text if 'SortList' in str_xml else None

        self.SortList.clear()
        if sort is not None:
            items: List[str] = sort.splitlines()
            for item in items:
                isPattern = False
                if item[-2:] == '-P':
                    item = item[:-2]
                    isPattern = True
                self.SortList.append(SortItem(item, isPattern))

        self.Alphabetical = bool(Et.fromstring(str_xml).find('Alphabetical').text) if 'Alphabetical' in str_xml else False

        # Getting the output anchor from Config.xml by the output connection name
        self.output = self.output_anchor_mgr.get_output_anchor('Output')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        self.output.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.record_copier: Sdk.RecordCopier = None
        self.record_creator: Sdk.RecordCreator = None

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Get the fields from the incoming connection
        fields: List[str] = []
        for field in record_info_in:
            fields.append(field.name)

        # Map each column of the input to where we want in the output.
        record_info_out = Sdk.RecordInfo(self.parent.alteryx_engine)
        self.record_copier = Sdk.RecordCopier(record_info_out, record_info_in)
        translations = sort_fields(fields, self.parent.SortList, self.parent.Alphabetical)
        for translation in translations:
            Sdk.Field = record_info_out.add_field(record_info_in.get_field_by_name(translation.name))
            self.record_copier.add(translation.index_to, translation.index_from)
        self.record_copier.done_adding()

        # Lets the downstream tools know what the outgoing record metadata will look like
        self.parent.output.init(record_info_out)

        # Creating a new, empty record creator based on record_info_out's record layout.
        self.record_creator = record_info_out.construct_record_creator()
        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        # Copy the data from the incoming record into the outgoing record.
        self.record_creator.reset()
        self.record_copier.copy(self.record_creator, in_record)
        out_record = self.record_creator.finalize_record()
        self.parent.output.push_record(out_record)
        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.output.update_progress(d_percent)

    def ii_close(self):
        # Close outgoing connections.
        self.parent.output.close()
