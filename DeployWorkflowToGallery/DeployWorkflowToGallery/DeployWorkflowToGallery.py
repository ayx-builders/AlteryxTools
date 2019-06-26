import json
import AlteryxPythonSDK as sdk
import xml.etree.ElementTree as Et
from SaveToGallery import save_to_gallery


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: sdk.AlteryxEngine = alteryx_engine

        # Custom properties
        self.input: IncomingInterface = None
        self.FileNameFieldName: str = None
        self.NameFieldName: str = None
        self.GalleryUrl: str = None
        self.ApiKey: str = None
        self.ApiSecret: str = None
        self.Owner: str = None

    def pi_init(self, str_xml: str):
        extractor = self.ParamExtractor(str_xml)
        self.FileNameFieldName = extractor.extract('FileNameField')
        self.NameFieldName = extractor.extract('NameField')
        self.GalleryUrl = extractor.extract('GalleryUrl')
        self.ApiKey = extractor.extract('ApiKey')
        self.ApiSecret = extractor.extract('ApiSecret')
        self.Owner = extractor.extract('Owner')

        if not self.params_are_valid():
            self.display_error_msg('Not all parameters were provided')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return False

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        return

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, sdk.EngineMessageType.error, msg_string)

    def display_info_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, sdk.EngineMessageType.info, msg_string)

    def params_are_valid(self) -> bool:
        for param in [self.FileNameFieldName, self.NameFieldName, self.GalleryUrl, self.ApiKey, self.ApiSecret, self.Owner]:
            if param is None:
                return False
        return True

    class ParamExtractor:
        def __init__(self, xml: str):
            self.xml = xml

        def extract(self, param: str):
            return Et.fromstring(self.xml).find(param).text if param in self.xml else None


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.IncomingRecordInfo: sdk.RecordInfo = None
        self.FileNameField: sdk.Field = None
        self.NameField: sdk.Field = None
        self.SuccessCount: int = 0
        self.FailCount: int = 0

    def ii_init(self, record_info_in: sdk.RecordInfo) -> bool:
        if not self.parent.params_are_valid():
            return False

        self.IncomingRecordInfo = record_info_in
        self.FileNameField = record_info_in.get_field_by_name(self.parent.FileNameFieldName)
        self.NameField = record_info_in.get_field_by_name(self.parent.NameFieldName)
        return True

    def ii_push_record(self, in_record: sdk.RecordRef) -> bool:
        file: str = self.FileNameField.get_as_string(in_record)
        name: str = self.NameField.get_as_string(in_record)
        secret: str = self.parent.alteryx_engine.decrypt_password(self.parent.ApiSecret, 0)
        response = save_to_gallery(self.parent.GalleryUrl, self.parent.ApiKey, secret, file,
                                   name, self.parent.Owner)
        if response.status_code != 200:
            self.FailCount += 1
            msg = response.results
            try:
                response_json = json.JSONDecoder().decode(response.results)
                if response_json['exceptionName'] is not None and response_json['message'] is not None:
                    msg = F"{response_json['exceptionName']}: {response_json['message']}"
            except:
                msg = str(response.results)
            self.parent.display_error_msg(msg)
            return False
        else:
            self.SuccessCount += 1
            return True

    def ii_update_progress(self, d_percent: float):
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

    def ii_close(self):
        if self.FailCount > 0:
            self.parent.display_error_msg(F"{self.SuccessCount} workflows were published successfully and"
                                          F"{self.FailCount} workflows failed to publish.")
        else:
            self.parent.display_info_msg(F"{self.SuccessCount} workflows were published successfully")
        return
