from .fields import ByteField, BytesField, IntegerField
from .packet import Packet


class DataPacket(Packet):
    frame_type = b"\xd5"
    destination = BytesField(1, 4)
    source = BytesField(5, 4)
