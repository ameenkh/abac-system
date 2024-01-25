from marshmallow import Schema, ValidationError, fields
from marshmallow.validate import Length, OneOf

# This file contains all the models of the server
# It's responsible for parsing and validating the input
# I chose Marshmallow library because its super fast and its dict to dict

MAX_ID_LENGTH = 256


class IdField(fields.String):
    def __init__(self, required=True, **additional_metadata):
        super().__init__(required=required, validate=Length(max=MAX_ID_LENGTH), **additional_metadata)


class AttributeNameField(fields.String):
    def __init__(self, **additional_metadata):
        super().__init__(required=True, validate=Length(max=MAX_ID_LENGTH), **additional_metadata)  # limiting the length to 256 in order to prevent memort crashed (like DDOS attacks)


class AttributeTypeField(fields.String):
    def __init__(self, **additional_metadata):
        super().__init__(required=True, validate=OneOf(["boolean", "string", "integer"]), **additional_metadata)


class OperatorField(fields.String):
    def __init__(self, **additional_metadata):
        super().__init__(required=True, validate=OneOf(["=", ">", "<", "starts_with"]), **additional_metadata)


class ValueField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str) or isinstance(value, bool) or isinstance(value, int):
            return value
        else:
            raise ValidationError('Field should be one of: string, boolean or integer')


class AttributeSchema(Schema):
    attribute_name = AttributeNameField()
    attribute_type = AttributeTypeField()


class UserSchema(Schema):
    attributes = fields.Dict(keys=AttributeNameField(), values=ValueField(required=True))


class PatchUserAttributeSchema(Schema):
    attribute_value = ValueField(required=True)


class PolicyData(Schema):
    attribute_name = AttributeNameField()
    operator = OperatorField()
    value = ValueField(required=True)


class PolicySchema(Schema):
    conditions = fields.List(fields.Nested(PolicyData()))


class ResourceSchema(Schema):
    policy_ids = fields.List(IdField())
