from .fields import Field, ByteField
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
import typing as _t


@_t.runtime_checkable
class PacketLike(_t.Protocol):
    def as_bytes(self) -> bytes:
        ...


class PacketMeta(type):
    def __new__(cls, name, bases, dct):
        for base in bases:
            for field in getattr(base, "_fields", []):
                if isinstance(field, Field) and field.end:
                    dct[field.name] = field
        fields = []
        last = 0
        for field in sorted(
            [
                v
                for v in dct.values()
                if isinstance(v, Field) and v.end is not None
            ],
            key=lambda x: x.offset,
        ):
            if field.offset != last:
                fields.append(Field(last, field.offset - last, name="Unknown"))
            fields.append(field)
            last = field.end
        fields.append(Field(last, None, name="tail"))
        dct["_fields"] = fields
        x = super().__new__(cls, name, bases, dct)
        return x


class Packet(metaclass=PacketMeta):
    packet_types = {}
    packet_type = ByteField(0)

    def __init__(self, bytes):
        self.bytes = bytes

    def as_bytes(self) -> bytes:
        return self.bytes

    @classmethod
    def from_bytes(cls, bytes):
        packet_type = bytes[0]
        if packet_type in cls.packet_types:
            cls = cls.packet_types[packet_type]
        return cls(bytes)

    @classmethod
    def register(cls, packet_type):
        def inner(packet_class):
            cls.packet_types[packet_type] = packet_class
            return packet_class

        return inner

    def __rich_console__(
        packet, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield f"{packet.__class__.__name__} Packet contains {len(packet.bytes)} bytes"
        t = Table("Offset", "Field Name", "Byte range", "Bytes", "Value")
        for field in packet._fields:
            t.add_row(
                f"{field.offset:3d}",
                field.name,
                f"{field.slice.start!s}-{field.slice.stop!s}",
                packet.bytes[field.slice].hex(),
                f"{getattr(packet,field.name,None)!r}",
            )
        yield (t)
