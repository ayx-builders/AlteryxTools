import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
import requests
import json
import time
import parse_read_operation


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr
        self.label = "OCR (" + str(n_tool_id) + ")"

        # Custom properties
        self.uploadFileField: str = None
        self.endpoint: str = None
        self.key: str = None
        self.output: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.uploadFileField = Et.fromstring(str_xml).find('UploadFileField').text if 'UploadFileField' in str_xml else None
        self.endpoint = Et.fromstring(str_xml).find('Endpoint').text if 'Endpoint' in str_xml else None
        self.key = Et.fromstring(str_xml).find('Key').text if 'Key' in str_xml else None
        if self.endpoint[-1] != "/":
            self.endpoint += "/"

        # Validity checks.
        if self.uploadFileField is None or self.endpoint is None or self.key is None:
            self.display_error_msg('One or more values were missing.')

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

    def display_info_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.record_creator: Sdk.RecordCreator = None
        self.uploadFileField: Sdk.Field = None
        self.output_info: Sdk.RecordInfo = None
        self.output_creator: Sdk.RecordCreator = None
        self.batch_read_url: str = None
        self.get_read_url: str = None

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        self.uploadFileField = record_info_in.get_field_by_name(self.parent.uploadFileField)
        self.output_info = self._generate_output_record_info()
        self.output_creator = self.output_info.construct_record_creator()
        self.batch_read_url = self.parent.endpoint + """vision/v2.0/read/core/asyncBatchAnalyze"""

        self.parent.output.init(self.output_info)
        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        update_only = self.parent.alteryx_engine.get_init_var(self.parent.n_tool_id, 'UpdateOnly') == 'True'
        if update_only:
            return True

        file_path = self.uploadFileField.get_as_string(in_record)
        with open(file_path, mode='rb') as file:
            upload_bytes = file.read()

        key = self._decrypt_value(self.parent.key)
        headers = {"Content-Type": "application/octet-stream", "Ocp-Apim-Subscription-Key": key}
        batch_response = requests.post(self.batch_read_url, data=upload_bytes, headers=headers)
        if batch_response.status_code != 202:
            self.parent.display_error_msg(batch_response.text)
            return False

        time.sleep(5)

        headers = {"Ocp-Apim-Subscription-Key": key}
        operation_location: str = batch_response.headers['Operation-Location']
        still_running = True
        while still_running:
            get_read_response = requests.get(operation_location, headers=headers)
            if get_read_response.status_code != 200:
                self.parent.display_error_msg(get_read_response.text)
                return False
            get_read_json = json.loads(get_read_response.content)
            if get_read_json['status'] == 'Failed':
                self.parent.display_error_msg("The text recognition process failed")
                return False
            if get_read_json['status'] == 'Succeeded':
                break
            time.sleep(5)

        results = parse_read_operation.parse_recognition_results(get_read_json['recognitionResults'])
        for result in results:
            self.output_info.get_field_by_name('FilePath').set_from_string(self.output_creator, file_path)
            self.output_info.get_field_by_name('Page').set_from_int64(self.output_creator, result.page)
            self.output_info.get_field_by_name('ClockwiseOrientation').set_from_double(self.output_creator, result.clockwiseOrientation)
            self.output_info.get_field_by_name('PageWidth').set_from_double(self.output_creator, result.pageWidth)
            self.output_info.get_field_by_name('PageHeight').set_from_double(self.output_creator, result.pageHeight)
            self.output_info.get_field_by_name('Unit').set_from_string(self.output_creator, result.unit)
            self.output_info.get_field_by_name('Text').set_from_string(self.output_creator, result.text)
            self.output_info.get_field_by_name('TopLeftX').set_from_double(self.output_creator, result.topLeftX)
            self.output_info.get_field_by_name('TopLeftY').set_from_double(self.output_creator, result.topLeftY)
            self.output_info.get_field_by_name('TopRightX').set_from_double(self.output_creator, result.topRightX)
            self.output_info.get_field_by_name('TopRightY').set_from_double(self.output_creator, result.topRightY)
            self.output_info.get_field_by_name('BottomRightX').set_from_double(self.output_creator, result.bottomRightX)
            self.output_info.get_field_by_name('BottomRightY').set_from_double(self.output_creator, result.bottomRightY)
            self.output_info.get_field_by_name('BottomLeftX').set_from_double(self.output_creator, result.bottomLeftX)
            self.output_info.get_field_by_name('BottomLeftY').set_from_double(self.output_creator, result.bottomLeftY)
            data = self.output_creator.finalize_record()
            self.parent.output.push_record(data)
            self.output_creator.reset()
        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.output.update_progress(d_percent)

    def ii_close(self):
        # Close outgoing connections.
        self.parent.output.close()

    def _generate_output_record_info(self) -> Sdk.RecordInfo:
        info: Sdk.RecordInfo = Sdk.RecordInfo(self.parent.alteryx_engine)
        info.add_field("FilePath", Sdk.FieldType.v_wstring, 1073741823, 0, self.parent.label)
        info.add_field("Page", Sdk.FieldType.int64, 0, 0, self.parent.label)
        info.add_field("ClockwiseOrientation", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("PageWidth", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("PageHeight", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("Unit", Sdk.FieldType.v_wstring, 10, 0, self.parent.label)
        info.add_field("Text", Sdk.FieldType.v_wstring, 1073741823, 0, self.parent.label)
        info.add_field("TopLeftX", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("TopLeftY", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("TopRightX", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("TopRightY", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("BottomRightX", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("BottomRightY", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("BottomLeftX", Sdk.FieldType.double, 0, 0, self.parent.label)
        info.add_field("BottomLeftY", Sdk.FieldType.double, 0, 0, self.parent.label)
        return info

    def _decrypt_value(self, value: str) -> str:
        return self.parent.alteryx_engine.decrypt_password(value)
