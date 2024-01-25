from typing import Any, Dict, List

from aiohttp import web
from marshmallow import ValidationError

_allowed_operators = {
    "string": {"=", ">", "<", "starts_with"},
    "boolean": {"="},
    "integer": {"=", ">", "<"}
}


def make_error(msg: str) -> Dict[str, Any]:
    return {"error": msg}


def assert_path_param_existence(request: web.Request, path_param: str) -> str:
    value = request.match_info.get(path_param)
    if not value:
        raise ValidationError(f"Missing required path param: {path_param}")
    return value


def validate_values_types(attributes_conf: Dict[str, str], attributes: Dict[str, Any]) -> None:
    for k, v in attributes.items():
        if k not in attributes_conf:
            raise ValidationError(f"attribute '{k}' was not found in global attributes")
        attribute_type = attributes_conf[k]
        match attribute_type:
            case "string":
                if not isinstance(v, str):
                    raise ValidationError(f"attribute '{k}' is not string")
            case "integer":
                if not isinstance(v, int):
                    raise ValidationError(f"attribute '{k}' is not integer")
            case "boolean":
                if not isinstance(v, bool):
                    raise ValidationError(f"attribute '{k}' is not boolean")


def validate_conditions_types(attributes_conf: Dict[str, str], conditions: List[Dict[str, Any]]) -> None:
    for cond in conditions:
        k = cond["attribute_name"]
        v = cond["value"]
        if k not in attributes_conf:
            raise ValidationError(f"attribute '{k}' was not found in global attributes")
        attribute_type = attributes_conf[k]

        if cond["operator"] not in _allowed_operators[attribute_type]:
            raise ValidationError(f'Cant apply operator "{cond["operator"]}" on {attribute_type}')

        match attribute_type:
            case "string":
                if not isinstance(v, str):
                    raise ValidationError(f"attribute '{k}' is not string")
            case "integer":
                if not isinstance(v, int):
                    raise ValidationError(f"attribute '{k}' is not integer")
            case "boolean":
                if not isinstance(v, bool):
                    raise ValidationError(f"attribute '{k}' is not boolean")


def apply(condition: Dict[str, Any], attributes: Dict[str, Any]) -> bool:
    if condition["attribute_name"] not in attributes:
        return False
    match condition["operator"]:
        case "=":
            return condition["value"] == attributes[condition["attribute_name"]]
        case ">":
            return condition["value"] < attributes[condition["attribute_name"]]
        case "<":
            return condition["value"] > attributes[condition["attribute_name"]]
        case "starts_with":
            return attributes[condition["attribute_name"]].startswith(condition["value"])
