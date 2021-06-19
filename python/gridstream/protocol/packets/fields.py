class Field:
    def __init__(self, offset, length, *, validators=None, name=None) -> None:
        self.offset = offset
        self.length = length
        self.validators = [] if validators is None else validators
        self.name = name

    @property
    def end(self):
        if self.length is None:
            return None
        return self.offset + self.length

    @property
    def slice(self):
        return slice(self.offset, self.end)

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.to_python(obj.bytes[self.slice])

    def __set__(self, obj, value):
        self.validate(value)
        # TODO: I don't think this will work as expected
        value = self.from_python(value)
        if self.length and len(value) != self.length:
            raise ValueError(
                f"Expected {self.length} bytes recieved {len(value)} bytes "
                f"[{value.hex()}] after conversion"
            )
        obj.bytes[self.slice] = value

    def validate(self, value):
        return all([validate(value) for validate in self.validators])

    def to_python(self, value):
        """This method should convert a sequence of bytes to a python value"""
        return value

    def from_python(self, value):
        """This method should convert a python value to a sequence of bytes"""
        return value


class ByteField(Field):
    def __init__(self, offset, *, validators=None):
        validators = [] if validators is None else validators
        super().__init__(
            offset, 1, validators=[lambda x: 0 <= x <= 255, *validators]
        )

    def to_python(self, value):
        return value[0]

    def from_python(self, value):
        return [value]


class BytesField(Field):
    pass


class IntegerField(Field):
    def __init__(
        self, offset, length, *, validators=None, order: str = "big"
    ) -> None:
        super().__init__(offset, length, validators=validators)
        self.order = order

    def to_python(self, value):
        return int.from_bytes(value, self.order)

    def from_python(self, value: int):
        value.to_bytes(self.length, self.order)
