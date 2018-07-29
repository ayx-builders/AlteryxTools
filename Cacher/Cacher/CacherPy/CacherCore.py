import AlteryxPythonSDK as Sdk


class Cacher:
    def __init__(self, engine, record_info: Sdk.RecordInfo):
        self.engine = engine
        self.record_info: Sdk.RecordInfo = record_info
        self.record_creator: Sdk.RecordCreator = record_info.construct_record_creator()


