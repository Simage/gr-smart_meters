from .fields import ByteField, BytesField, IntegerField
from .packet import Packet


class RoutingPacket(Packet):
    frame_type = b"\x55"
    destination = BytesField(1, 6)
    source = BytesField(7, 6)


@RoutingPacket.register(0x30)
class ARPPacket(RoutingPacket):
    sequence = ByteField(13)
    uptime = IntegerField(14, 4)
    lan_address = BytesField(20, 4)
    timing = IntegerField(29, 2)
