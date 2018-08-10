import AlteryxPythonSDK as Sdk
import collections
import struct
from typing import List
import CacherPy.CacherIo as Io


size_len = 4
ProcessorMethods = collections.namedtuple("ProcessorMethods", "write read")
ReadResult = collections.namedtuple("ReadResult", "did_read data")


class Cacher:
    def __init__(self, tool_id: int, engine: Sdk.AlteryxEngine, info: Sdk.RecordInfo, max_size: int):
        self.engine = engine
        self.tool_id = tool_id
        self.record_info: Sdk.RecordInfo = info
        self.record_creator: Sdk.RecordCreator = self.record_info.construct_record_creator()
        self.current_record: Sdk.RecordRef = None
        self.io: Io.CacherIo = Io.CacherIo(max_size, engine.create_temp_file_name())
        self.fields: List[Sdk.Field] = []
        i = 0
        while i < info.num_fields:
            self.fields.append(info[i])
            i += 1

        self.num_fields = i
        self.processorMap = {
            Sdk.FieldType.wstring: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                    self._get_read_function(self._read_string_field)),
            Sdk.FieldType.v_wstring: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                      self._get_read_function(self._read_string_field)),
            Sdk.FieldType.string: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                   self._get_read_function(self._read_string_field)),
            Sdk.FieldType.v_string: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                     self._get_read_function(self._read_string_field)),
            Sdk.FieldType.datetime: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                     self._get_read_function(self._read_string_field)),
            Sdk.FieldType.time: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                 self._get_read_function(self._read_string_field)),
            Sdk.FieldType.date: ProcessorMethods(self._get_write_function(self._write_string_field),
                                                 self._get_read_function(self._read_string_field)),
            Sdk.FieldType.float: ProcessorMethods(self._get_write_function(self._write_decimal_field),
                                                  self._get_read_function(self._read_decimal_field)),
            Sdk.FieldType.fixeddecimal: ProcessorMethods(self._get_write_function(self._write_decimal_field),
                                                         self._get_read_function(self._read_decimal_field)),
            Sdk.FieldType.double: ProcessorMethods(self._get_write_function(self._write_decimal_field),
                                                   self._get_read_function(self._read_decimal_field)),
            Sdk.FieldType.int16: ProcessorMethods(self._get_write_function(self._write_int_field(2)),
                                                  self._get_read_function(self._read_int_field(2))),
            Sdk.FieldType.int32: ProcessorMethods(self._get_write_function(self._write_int_field(4)),
                                                  self._get_read_function(self._read_int_field(4))),
            Sdk.FieldType.int64: ProcessorMethods(self._get_write_function(self._write_int_field(8)),
                                                  self._get_read_function(self._read_int_field(8))),
            Sdk.FieldType.byte: ProcessorMethods(self._get_write_function(self._write_int_field(1)),
                                                 self._get_read_function(self._read_int_field(1))),
            Sdk.FieldType.bool: ProcessorMethods(self._get_write_function(self._write_int_field(1)),
                                                 self._get_read_function(self._read_int_field(1))),
            Sdk.FieldType.blob: ProcessorMethods(self._get_write_function(self._write_byte_field),
                                                 self._get_read_function(self._read_byte_field)),
            Sdk.FieldType.spatialobj: ProcessorMethods(self._get_write_function(self._write_byte_field),
                                                       self._get_read_function(self._read_byte_field)),
            Sdk.FieldType.unknown: ProcessorMethods(self._get_write_function(self._write_byte_field),
                                                    self._get_read_function(self._read_byte_field)),
        }

    def push(self, data: Sdk.RecordRef):
        i = 0
        while i < self.num_fields:
            field = self.fields[i]
            self.processorMap[field.type].write(field, data)
            i += 1

    def start_read(self):
        self.io.start_read()

    def restart_append(self):
        self.io.restart_append()

    def read(self) -> bool:
        i: int = 0
        self.record_creator.reset()
        while i < self.num_fields:
            field: Sdk.Field = self.fields[i]
            result = self.processorMap[field.type].read(field)
            if not result:
                return False
            i += 1

        self.current_record = self.record_creator.finalize_record()
        return True

    def close(self):
        self.io.close()

    def _get_write_function(self, writer):
        def local_writer(field: Sdk.Field, data: Sdk.RecordRef):
            if self._write_if_null(field, data):
                return

            writer(field, data)

        return local_writer

    def _write_byte_field(self, field: Sdk.Field, data: Sdk.RecordRef):
        data_bytes = field.get_as_blob(data)
        data_size = len(data_bytes)
        data_size_bytes = data_size.to_bytes(size_len, byteorder='big')
        self.io.write(data_size_bytes)
        self.io.write(data_bytes)

    def _write_decimal_field(self, field: Sdk.Field, data: Sdk.RecordRef):
        data_bytes = struct.pack('d', field.get_as_double(data))
        self.io.write(data_bytes)

    def _write_int_field(self, byte_len: int):
        def write_sized_int_field(field: Sdk.Field, data: Sdk.RecordRef):
            if byte_len == 8:
                getter = field.get_as_int64
            else:
                getter = field.get_as_int32
            data_bytes = getter(data).to_bytes(byte_len, byteorder='big')
            self.io.write(data_bytes)

        return write_sized_int_field

    def _write_string_field(self, field: Sdk.Field, data: Sdk.RecordRef):
        data_bytes = field.get_as_string(data).encode('utf-8')
        data_size = len(data_bytes)
        data_size_bytes = data_size.to_bytes(size_len, byteorder='big')
        self.io.write(data_size_bytes)
        self.io.write(data_bytes)

    def _get_read_function(self, reader):
        def local_reader(field: Sdk.Field):
            is_null: bool = self._read_is_null()
            if is_null is None:
                return False
            elif is_null:
                field.set_null(self.record_creator)
                return True
            else:
                return reader(field)

        return local_reader

    def _read_byte_field(self, field: Sdk.Field) -> bool:
        byte_size = self._read_bytes(size_len)
        if not byte_size[0]:
            return False

        size = int.from_bytes(byte_size[1], byteorder='big')
        byte_data = bytes(self.io.read(size))
        field.set_from_blob(self.record_creator, byte_data)
        return True

    def _read_decimal_field(self, field: Sdk.Field) -> bool:
        byte_data = self._read_bytes(8)
        if not byte_data[0]:
            return False

        data_tuple = struct.unpack("d", byte_data[1])
        data: float = float(data_tuple[0])
        field.set_from_double(self.record_creator, data)
        return True

    def _read_int_field(self, byte_len: int):
        def read_sized_int_field(field: Sdk.Field) -> bool:
            byte_data = self._read_bytes(byte_len)
            if not byte_data[0]:
                return False

            data: int = int.from_bytes(byte_data[1], byteorder='big')
            if byte_len == 8:
                setter = field.set_from_int64
            else:
                setter = field.set_from_int32
            setter(self.record_creator, data)
            return True

        return read_sized_int_field

    def _read_string_field(self, field: Sdk.Field):
        size_bytes = self._read_bytes(size_len)
        if not size_bytes[0]:
            return False

        size = int.from_bytes(size_bytes[1], byteorder='big')
        data_bytes = self._read_bytes(size)
        if data_bytes[0]:
            data: str = data_bytes[1].decode('utf-8')
            field.set_from_string(self.record_creator, data)
            return True
        else:
            return False

    def _read_bytes(self, number_of_bytes: int) -> ReadResult:
        data = self.io.read(number_of_bytes)
        if data == b'':
            self.current_record = None
            return ReadResult(False, None)

        return ReadResult(True, data)

    def _write_if_null(self, field: Sdk.Field, data: Sdk.RecordRef) -> bool:
        if field.get_null(data):
            self.io.write(int(1).to_bytes(1, byteorder='big'))
            return True
        else:
            self.io.write(int(0).to_bytes(1, byteorder='big'))
            return False

    def _read_is_null(self) -> bool:
        result: bytes = self.io.read(1)
        if result == b'':
            return None
        else:
            is_null = int.from_bytes(result, byteorder='big')
            if is_null == 1:
                return True
            else:
                return False
