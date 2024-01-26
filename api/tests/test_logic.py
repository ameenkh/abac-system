from typing import Any, Dict

import pytest
from marshmallow import ValidationError

from api.common.utils import apply, validate_conditions_types, validate_values_types


@pytest.mark.parametrize("age", [None, "", "some string", {}, {"k": "v"}, True, False])
def test_validate_values_types_integer(age: Any) -> None:
    attributes_conf = {
        "age": "integer"
    }
    with pytest.raises(ValidationError) as err:
        validate_values_types(attributes_conf, {"age": age})
    assert str(err.value) == "attribute 'age' is not integer"


@pytest.mark.parametrize("is_manager", [None, "", "some string", {}, {"k": "v"}, 0, 123])
def test_validate_values_types_boolean(is_manager: Any) -> None:
    attributes_conf = {
        "is_manager": "boolean"
    }
    with pytest.raises(ValidationError) as err:
        validate_values_types(attributes_conf, {"is_manager": is_manager})
    assert str(err.value) == "attribute 'is_manager' is not boolean"


@pytest.mark.parametrize("name", [None, {}, {"k": "v"}, 0, 123, True, False])
def test_validate_values_types_string(name: Any) -> None:
    attributes_conf = {
        "name": "string"
    }
    with pytest.raises(ValidationError) as err:
        validate_values_types(attributes_conf, {"name": name})
    assert str(err.value) == "attribute 'name' is not string"


def test_validate_values_types_unknown() -> None:
    attributes_conf = {
        "name": "something else"
    }
    with pytest.raises(ValidationError) as err:
        validate_values_types(attributes_conf, {"name": "name"})
    assert str(err.value) == "attribute 'name' of type 'something else' is not supported"


@pytest.mark.parametrize("operator", [">", "<", "starts_with"])
def test_validate_conditions_types_boolean_operator(operator: str) -> None:
    attributes_conf = {
        "is_manager": "boolean"
    }
    conditions = [
        {
            "attribute_name": "is_manager",
            "operator": operator,
            "value": True
        }
    ]
    with pytest.raises(ValidationError) as err:
        validate_conditions_types(attributes_conf, conditions)
    assert str(err.value) == f'Cant apply operator "{operator}" on boolean'


@pytest.mark.parametrize("operator", ["starts_with"])
def test_validate_conditions_types_integer_operator(operator: str) -> None:
    attributes_conf = {
        "age": "integer"
    }
    conditions = [
        {
            "attribute_name": "age",
            "operator": operator,
            "value": 30
        }
    ]
    with pytest.raises(ValidationError) as err:
        validate_conditions_types(attributes_conf, conditions)
    assert str(err.value) == f'Cant apply operator "{operator}" on integer'


def test_validate_conditions_types_integer_value() -> None:
    attributes_conf = {
        "age": "integer"
    }
    conditions = [
        {
            "attribute_name": "age",
            "operator": "=",
            "value": "some string"
        }
    ]
    with pytest.raises(ValidationError) as err:
        validate_conditions_types(attributes_conf, conditions)
    assert str(err.value) == "attribute 'age' is not integer"


def test_validate_conditions_types_boolean_value() -> None:
    attributes_conf = {
        "is_manager": "boolean"
    }
    conditions = [
        {
            "attribute_name": "is_manager",
            "operator": "=",
            "value": "some string"
        }
    ]
    with pytest.raises(ValidationError) as err:
        validate_conditions_types(attributes_conf, conditions)
    assert str(err.value) == "attribute 'is_manager' is not boolean"


def test_validate_conditions_types_string_value() -> None:
    attributes_conf = {
        "name": "string"
    }
    conditions = [
        {
            "attribute_name": "name",
            "operator": "=",
            "value": 30
        }
    ]
    with pytest.raises(ValidationError) as err:
        validate_conditions_types(attributes_conf, conditions)
    assert str(err.value) == "attribute 'name' is not string"


@pytest.mark.parametrize(
    "condition,attributes",
    [
        ({"attribute_name": "age","operator": ">","value": 30}, {"age": 31}),
        ({"attribute_name": "age","operator": "=","value": 30}, {"age": 30}),
        ({"attribute_name": "age","operator": "<","value": 30}, {"age": 29}),
        ({"attribute_name": "is_manager","operator": "=","value": True}, {"is_manager": True}),
        ({"attribute_name": "is_manager","operator": "=","value": False}, {"is_manager": False}),
        ({"attribute_name": "name","operator": "=","value": "John"}, {"name": "John"}),
        ({"attribute_name": "name","operator": "starts_with","value": "John"}, {"name": "John Smith"}),
        ({"attribute_name": "name","operator": ">","value": "a"}, {"name": "b"}),
        ({"attribute_name": "name","operator": "<","value": "b"}, {"name": "a"}),
    ]
)
def test_apply_true(condition: Dict[str, Any], attributes: Dict[str, Any]) -> None:
    assert apply(condition, attributes)


@pytest.mark.parametrize(
    "condition,attributes",
    [
        ({"attribute_name": "age","operator": ">","value": 30}, {}),
({"attribute_name": "age","operator": ">","value": 30}, {"age": 30}),
        ({"attribute_name": "age","operator": "=","value": 30}, {"age": 31}),
        ({"attribute_name": "age","operator": "<","value": 30}, {"age": 31}),
        ({"attribute_name": "is_manager","operator": "=","value": True}, {"is_manager": False}),
        ({"attribute_name": "is_manager","operator": "=","value": False}, {"is_manager": True}),
        ({"attribute_name": "name","operator": "=","value": "John"}, {"name": "Smith"}),
        ({"attribute_name": "name","operator": "starts_with","value": "John"}, {"name": "Jo2hn Smith"}),
        ({"attribute_name": "name","operator": ">","value": "a"}, {"name": "a"}),
        ({"attribute_name": "name","operator": "<","value": "a"}, {"name": "a"}),
    ]
)
def test_apply_false(condition: Dict[str, Any], attributes: Dict[str, Any]) -> None:
    assert not apply(condition, attributes)
