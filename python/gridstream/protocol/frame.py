from .packets import Packet, PacketLike, DataPacket, RoutingPacket
import typing as _t
from binascii import crc_hqx as crc16

class FrameError(Exception):pass
class ValidationError(FrameError):pass

class Frame:
    frame_types = {}
    packet_class = Packet
    _initial_crc = None

    @classmethod
    def register(cls, frame_type):
        def inner(frame_class):
            cls.frame_types[frame_type] = frame_class
            return frame_class

        return inner

    @classmethod
    def set_initial_checksum(cls, initial_checksum):
        cls._initial_crc = initial_checksum

    def __init__(
        self,
        header: bytes,
        type: int,
        length: _t.Optional[int] = None,
        data: _t.Optional[_t.Union[str, bytes, PacketLike]] = None,
        checksum: _t.Optional[int] = None,
        validate: bool = True,
    ):
        self._packet = None
        self.header = header
        self.type = type
        if length is None:
            self._set_data_bytes(data)
        else:
            if data is None:
                self.data_bytes = bytes([b"\x00" for i in range(length)])
            else:
                self._set_data_bytes(data)
        self.length = length
        if validate:
            self.validate(checksum=checksum)
        self.length = len(self.data_bytes)

    def validate(self, checksum=None):
        if self.header != b"\x00\xff\x2a":
            raise ValidationError("Invalid Header")
        if len(self.data_bytes) != self.length:
            raise ValidationError(
                f"Provided Length ({self.length}) does not match "
                f"length of data ({len(self.data_bytes)})"
            )
        if checksum is not None:
            ck_sum = self.generate_checksum()
            if ck_sum != checksum:
                raise ValidationError(
                    "Provided checksum does not match generated checksum "
                    f"(0x{checksum:04x}!=0x{ck_sum:04x})"
                )

    @property
    def packet(self):
        if self._packet is None:
            self._packet = self.packet_class.from_bytes(self.data_bytes)
        return self._packet

    def generate_checksum(self):
        return crc16(self.data_bytes, self._initial_crc)

    def _set_data_bytes(self, data: _t.Union[str, bytes, PacketLike]):
        if isinstance(data, Packet):
            self._packet
            self.data_bytes = data.as_bytes()
        elif isinstance(data, str):
            self.data_bytes = bytes.fromhex(data)
        elif isinstance(data, bytes):
            self.data_bytes = data
        else:
            raise FrameError(f"Unable to set Frame.data_bytes from {data!r}")

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        validate_checksum: bool = True,
        validate: bool = True,
    ):
        header = data[:3]
        frame_type = data[3]
        frame_length = int.from_bytes(data[4:6], "big")
        packet_length = frame_length - 2
        packet_data = data[6 : packet_length + 6]
        checksum = int.from_bytes(
            data[frame_length + 4 : frame_length + 6], "big"
        )
        if frame_type in cls.frame_types:
            cls = cls.frame_types[frame_type]
        return cls(
            header,
            frame_type,
            packet_length,
            packet_data,
            checksum if validate_checksum else None,
            validate=validate,
        )


@Frame.register(0x55)
class RoutingFrame(Frame):
    packet_class = RoutingPacket


@Frame.register(0xD5)
class DataFrame(Frame):
    packet_class = DataPacket
