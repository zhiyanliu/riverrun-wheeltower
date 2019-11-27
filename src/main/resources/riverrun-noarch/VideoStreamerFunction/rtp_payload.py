from pkg_resources import parse_version
from kaitaistruct import __version__ as ks_version, KaitaiStruct
from enum import IntEnum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))


class RTPPayload(KaitaiStruct):

    class NALUnitTypeEnum(IntEnum):
        unassigned1 = 0
        slice = 1
        dp_a = 2
        dp_b = 3
        dp_c = 4
        idr = 5
        sei = 6
        sps = 7
        pps = 8
        aud = 9
        eof_seq = 10
        eof_stream = 11
        fill = 12
        reserved1 = 13
        reserved2 = 14
        reserved3 = 15
        reserved4 = 16
        reserved5 = 17
        reserved6 = 18
        reserved7 = 19
        reserved8 = 20
        reserved9 = 21
        reserved10 = 22
        reserved11 = 23

        @classmethod
        def has_value(cls, value):
            return value in cls._value2member_map_

    class PayloadTypeEnum(IntEnum):
        # equals nal unit type (cannot extend enumerations in python)
        unassigned1 = 0
        slice = 1
        dp_a = 2
        dp_b = 3
        dp_c = 4
        idr = 5
        sei = 6
        sps = 7
        pps = 8
        aud = 9
        eof_seq = 10
        eof_stream = 11
        fill = 12
        reserved1 = 13
        reserved2 = 14
        reserved3 = 15
        reserved4 = 16
        reserved5 = 17
        reserved6 = 18
        reserved7 = 19
        reserved8 = 20
        reserved9 = 21
        reserved10 = 22
        reserved11 = 23
        # other payload types
        stap_a = 24
        stap_b = 25
        mtap_16 = 26
        mtap_24 = 27
        fu_a = 28
        fu_b = 29

    def __init__(self, _io, _parent=None, _root=None):
        super(RTPPayload, self).__init__(_io)
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.f = self._io.read_bits_int(1)
        self.nri = self._io.read_bits_int(2)
        self.type = self._root.PayloadTypeEnum(self._io.read_bits_int(5))

        if self._root.NALUnitTypeEnum.has_value(self.type):  # single NAL unit
            self.fragment_nal_unit = False
            self.nal_unit_type = self._root.NALUnitTypeEnum(int(self.type))
        elif self.type == self._root.PayloadTypeEnum.fu_a:   # FU-A fragmentation
            self.fragment_nal_unit = True
            self.start_bit = self._io.read_bits_int(1)
            self.end_bit = self._io.read_bits_int(1)
            self.reserved_bit = self._io.read_bits_int(1)
            self.nal_unit_type = self._root.NALUnitTypeEnum(self._io.read_bits_int(5))
        else:
            raise Exception("unsupported RTP payload type, type = %d" % self.type)

        self.data = self._io.read_bytes(self._io.size() - self._io.pos())
