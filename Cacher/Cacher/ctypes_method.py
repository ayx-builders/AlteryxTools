import AlteryxPythonSDK as Sdk
from typing import Set, Any


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        self.n_tool_id = n_tool_id
        self.alteryx_engine = alteryx_engine
        self.output_anchor_mgr = output_anchor_mgr

        self.is_initialized = True

    def pi_init(self, str_xml: str):
        self.output_anchor = self.output_anchor_mgr.get_output_anchor('Output')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.single_input = IncomingInterface(self)
        return self.single_input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        return False  # must always have an input

    def pi_close(self, b_has_errors: bool):
        self.output_anchor.assert_close()


import ctypes


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


class RecordRefWrapper():
    def __init__(self, record):
        record_struct = RecordRefStruct.wrap(record)
        self.data_addr = ctypes.c_uint64.from_address(record_struct.p3).value

    def read_int64(self):
        v = ctypes.c_uint64.from_address(self.data_addr).value
        self.data_addr += 8 + 1
        return v

    def read_string(self):
        v = ctypes.cast(self.data_addr, ctypes.c_char_p).value
        self.data_addr += len(v) + 1
        return v.decode("ascii")


class IncomingInterface:
    def __init__(self, parent: object):
        self.parent = parent

        self.record_creator = None
        self.record_info_out = None

    def ii_init(self, record_info_in: object) -> bool:
        if not self.parent.is_initialized:
            return False

        self.record_info_in = list(record_info_in)
        record_info_out = Sdk.RecordInfo(self.parent.alteryx_engine)
        for idx, field in enumerate(self.record_info_in):
            record_info_out.add_field(field.name, field.type, field.size, field.scale)
        self.parent.output_anchor.init(record_info_out)
        self.record_creator = record_info_out.construct_record_creator()
        return True

    def ii_push_record(self, record: object) -> bool:
        if not self.parent.is_initialized:
            return False

        rc = self.record_creator
        rc.reset()
        ri = self.record_info_in

        r = RecordRefWrapper(record)
        ri[0].set_from_int64(rc, r.read_int64())  # assumes input record is int64,int64,int64,int64,string,string,string
        ri[1].set_from_int64(rc, r.read_int64())  # if your data format changes then good luck
        ri[2].set_from_int64(rc, r.read_int64())
        ri[3].set_from_int64(rc, r.read_int64())
        ri[4].set_from_string(rc, r.read_string())
        ri[5].set_from_string(rc, r.read_string())
        ri[6].set_from_string(rc, r.read_string())

        record_out = rc.finalize_record()

        return self.parent.output_anchor.push_record(record_out)  # propagate error flag

    def ii_update_progress(self, d_percent: float):
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)
        self.parent.output_anchor.update_progress(d_percent)

    def ii_close(self):
        self.parent.output_anchor.close()