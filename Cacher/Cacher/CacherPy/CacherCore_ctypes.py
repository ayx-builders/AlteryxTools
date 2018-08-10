import AlteryxPythonSDK as Sdk
import collections
import struct
from typing import List
import CacherPy.CacherIo as Io
import ctypes


size_len = 4
ProcessorMethods = collections.namedtuple("ProcessorMethods", "write read")
ReadResult = collections.namedtuple("ReadResult", "did_read data")


class PyVarObjectStruct(ctypes.Structure):
    _fields_ = [('ob_refcnt', ctypes.c_ssize_t),
                ('ob_type', ctypes.c_void_p),
                ('ob_size', ctypes.c_ssize_t)]


class RecordRefStruct(PyVarObjectStruct):
    _fields_ = [("n1", ctypes.c_void_p),  # 0
                ("n2", ctypes.c_void_p),  # 0
                ("p1", ctypes.c_void_p),  # &p2
                ("p2", ctypes.c_void_p),
                ("n3", ctypes.c_void_p),  # 0
                ("p3", ctypes.c_void_p),  # dig here
                ("p4", ctypes.c_void_p)]

    def __repr__(self):
        return (
            f"RecordRefStruct(p1={self.p1},p2={self.p2},p3={self.p3},p4={self.p4} ,n1={self.n1},n2={self.n2},n3={self.n3})")

    @classmethod
    def wrap(cls, obj):
        assert isinstance(obj, Sdk.RecordRef)
        return cls.from_address(id(obj))


class RecordRefWrapper:
    def __init__(self, record):
        self.record = record
        self.record_struct = RecordRefStruct.wrap(record)
        self.data_addr = ctypes.c_uint64.from_address(self.record_struct.p3).value

    def read_string(self, size: int):
        v = ctypes.cast(self.data_addr, ctypes.c_char_p).value
        self.data_addr += size + 1
        return v

    def read_variable_string(self):
        v = ctypes.cast(self.data_addr, ctypes.c_char_p).value
        self.data_addr += (len(v) * 2) + 2
        return v

    def read_int16(self):
        v = ctypes.c_uint16.from_address(self.data_addr).value
        self.data_addr += 3
        return v.to_bytes(2, byteorder='big')

    def read_int32(self):
        v = ctypes.c_uint32.from_address(self.data_addr).value
        self.data_addr += 5
        return v.to_bytes(4, byteorder='big')

    def read_int64(self):
        v = ctypes.c_uint64.from_address(self.data_addr).value
        self.data_addr += 9
        return v.to_bytes(8, byteorder='big')

    def read_decimal(self, size: int):
        v = ctypes.cast(self.data_addr, ctypes.c_char_p).value
        self.data_addr += size + 1
        return v

    def read_byte(self):
        v = ctypes.c_byte.from_address(self.data_addr).value
        self.data_addr += 2
        return v.to_bytes(1, byteorder='big')

    def read_blob(self):
        v = ctypes.cast(self.data_addr, ctypes.c_char_p).value
        self.data_addr += len(v) + 1
        return v


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
            Sdk.FieldType.wstring: ProcessorMethods(self._write_unicode,
                                                    self._read_unicode),
            Sdk.FieldType.v_wstring: ProcessorMethods(self._write_variable_string,
                                                      self._read_unicode),
            Sdk.FieldType.string: ProcessorMethods(self._write_ascii,
                                                   self._read_ascii),
            Sdk.FieldType.v_string: ProcessorMethods(self._write_variable_string,
                                                     self._read_ascii),
            Sdk.FieldType.datetime: ProcessorMethods(self._write_ascii,
                                                     self._read_ascii),
            Sdk.FieldType.time: ProcessorMethods(self._write_ascii,
                                                 self._read_ascii),
            Sdk.FieldType.date: ProcessorMethods(self._write_ascii,
                                                 self._read_ascii),
            Sdk.FieldType.float: ProcessorMethods(self._write_decimal,
                                                  self._read_decimal),
            Sdk.FieldType.fixeddecimal: ProcessorMethods(self._write_ascii,
                                                         self._read_ascii),
            Sdk.FieldType.double: ProcessorMethods(self._write_decimal,
                                                   self._read_decimal),
            Sdk.FieldType.int16: ProcessorMethods(self._write_int16,
                                                  self._read_int16),
            Sdk.FieldType.int32: ProcessorMethods(self._write_int32,
                                                  self._read_int32),
            Sdk.FieldType.int64: ProcessorMethods(self._write_int64,
                                                  self._read_int64),
            Sdk.FieldType.byte: ProcessorMethods(self._write_byte,
                                                 self._read_byte),
            Sdk.FieldType.bool: ProcessorMethods(self._write_byte,
                                                 self._read_byte),
            Sdk.FieldType.blob: ProcessorMethods(self._write_blob,
                                                 self._read_blob),
            Sdk.FieldType.spatialobj: ProcessorMethods(self._write_blob,
                                                       self._read_blob),
            Sdk.FieldType.unknown: ProcessorMethods(self._write_blob,
                                                    self._read_blob),
        }

    def push(self, data: Sdk.RecordRef):
        wrapper = RecordRefWrapper(data)
        i = 0
        self.io.write(b'0')
        while i < self.num_fields:
            field = self.fields[i]
            self.processorMap[field.type].write(wrapper, field)
            i += 1

    def start_read(self):
        self.io.start_read()

    def restart_append(self):
        self.io.restart_append()

    def read(self) -> bool:
        i: int = 0
        self.record_creator.reset()
        record_check = self.io.read(1)
        if record_check == b'':
            return False

        while i < self.num_fields:
            field: Sdk.Field = self.fields[i]
            self.processorMap[field.type].read(field)
            i += 1

        self.current_record = self.record_creator.finalize_record()
        return True

    def close(self):
        self.io.close()

    def _write_has_data(self, wrapper: RecordRefWrapper, field: Sdk.Field) -> bool:
        if field.get_null(wrapper.record):
            self.io.write(b'0')
            return False
        else:
            self.io.write(b'1')
            return True

    def _write_unicode(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        data_bytes = wrapper.read_string(field.size * 2)
        if self._write_has_data(wrapper, field):
            self._write_string_bytes(data_bytes)

    def _write_ascii(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        data_bytes = wrapper.read_string(field.size)
        if self._write_has_data(wrapper, field):
            self._write_string_bytes(data_bytes)

    def _write_variable_string(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        data_bytes = wrapper.read_variable_string()
        if self._write_has_data(wrapper, field):
            self._write_string_bytes(data_bytes)

    def _write_string_bytes(self, data_bytes: bytes):
        size = len(data_bytes)
        size_bytes = size.to_bytes(size_len, byteorder='big')
        self.io.write(size_bytes)
        self.io.write(data_bytes)

    def _write_decimal(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        size = 8
        if field.type == Sdk.FieldType.float:
            size = 4

        if self._write_has_data(wrapper, field):
            data_bytes = wrapper.read_decimal(size)
            self.io.write(data_bytes)

    def _write_int16(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        if self._write_has_data(wrapper, field):
            self.io.write(wrapper.read_int16())

    def _write_int32(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        if self._write_has_data(wrapper, field):
            self.io.write(wrapper.read_int32())

    def _write_int64(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        if self._write_has_data(wrapper, field):
            self.io.write(wrapper.read_int64())

    def _write_byte(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        if self._write_has_data(wrapper, field):
            data_bytes = wrapper.read_byte()
            self.engine.output_message(self.tool_id, Sdk.EngineMessageType.info,
                                       "byte: %s" % str(data_bytes))
            self.io.write(data_bytes)

    def _write_blob(self, wrapper: RecordRefWrapper, field: Sdk.Field):
        data_bytes = wrapper.read_blob()
        size = len(data_bytes)
        size_bytes = size.to_bytes(size_len, byteorder='big')
        self.io.write(size_bytes)
        self.io.write(data_bytes)

    def _read_has_data(self, field: Sdk.Field) -> bool:
        has_data = self.io.read(1)
        if has_data == b'1':
            return True
        else:
            field.set_null(self.record_creator)
            return False

    def _read_unicode(self, field: Sdk.Field):
        if self._read_has_data(field):
            size_bytes = self.io.read(size_len)
            size = int.from_bytes(size_bytes, byteorder='big')
            data_bytes = self.io.read(size)
            data = data_bytes.decode('utf-8')
            field.set_from_string(self.record_creator, data)

    def _read_ascii(self, field: Sdk.Field):
        if self._read_has_data(field):
            size_bytes = self.io.read(size_len)
            size = int.from_bytes(size_bytes, byteorder='big')
            data_bytes = self.io.read(size)
            data = data_bytes.decode('ascii')
            field.set_from_string(self.record_creator, data)

    def _read_int16(self, field: Sdk.Field):
        if self._read_has_data(field):
            data_bytes = self.io.read(2)
            data = int.from_bytes(data_bytes, byteorder='big')
            field.set_from_int32(self.record_creator, data)

    def _read_int32(self, field: Sdk.Field):
        if self._read_has_data(field):
            data_bytes = self.io.read(4)
            data = int.from_bytes(data_bytes, byteorder='big')
            field.set_from_int32(self.record_creator, data)

    def _read_int64(self, field: Sdk.Field):
        if self._read_has_data(field):
            data_bytes = self.io.read(8)
            data = int.from_bytes(data_bytes, byteorder='big')
            field.set_from_int64(self.record_creator, data)

    def _read_decimal(self, field: Sdk.Field):
        if self._read_has_data(field):
            size = 8
            dec_format = "d"
            if field.type == Sdk.FieldType.float:
                size = 4
                dec_format = "f"

            data_bytes = self.io.read(size)
            data: float = struct.unpack(dec_format, data_bytes)[0]
            field.set_from_double(self.record_creator, data)

    def _read_byte(self, field: Sdk.Field):
        if self._read_has_data(field):
            data_bytes = self.io.read(1)
            data = bool.from_bytes(data_bytes, byteorder='big')
            field.set_from_bool(self.record_creator, data)

    def _read_blob(self, field: Sdk.Field):
        size_bytes = self.io.read(size_len)
        size = int.from_bytes(size_bytes, byteorder='big')
        data_bytes = self.io.read(size)
        self.engine.output_message(self.tool_id, Sdk.EngineMessageType.info, str(data_bytes))
        field.set_from_blob(self.record_creator, data_bytes)
