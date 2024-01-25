from typing import Any, Dict, List

from bson import ObjectId

from api.common.exceptions import DuplicateKeyError, NotFoundError

_ATTRIBUTES: Dict[str, str] = {}
_USERS: Dict[ObjectId, Dict[str, Any]] = {}
_POLICIES: Dict[ObjectId, List[Dict[str, Any]]] = {}
_RESOURCES: Dict[ObjectId, List[ObjectId]] = {}


def print_all():
    print(f"\n\n{_USERS=}\n{_POLICIES=}\n{_RESOURCES=}\n\n")


async def get_attribute(attribute_name: str) -> Dict[str, str]:
    if attribute_name not in _ATTRIBUTES:
        raise NotFoundError(f"attribute: '{attribute_name}' was not found")

    return {
        "attribute_name": attribute_name,
        "attribute_type": _ATTRIBUTES[attribute_name]
    }


async def create_attribute(attribute_name: str, attribute_type: str) -> None:
    if attribute_name in _ATTRIBUTES:
        raise DuplicateKeyError(f"attribute: {attribute_name} already exists")

    _ATTRIBUTES[attribute_name] = attribute_type


async def create_user(attributes: Dict[str, Any]) -> ObjectId:
    user_id = ObjectId()
    _USERS[user_id] = attributes
    return user_id


async def get_user(user_id: ObjectId) -> Dict[str, Any]:
    if user_id not in _USERS:
        raise NotFoundError(f"user: '{user_id}' was not found")

    return {
        "user_id": user_id,
        "attributes": _USERS[user_id].copy()
    }


async def override_user_attributes(user_id: ObjectId, attributes: Dict[str, Any]) -> None:
    if user_id not in _USERS:
        raise NotFoundError(f"user: '{user_id}' was not found")
    _USERS[user_id] = attributes


async def patch_user_attribute(user_id: ObjectId, attribute_name: str, attribute_value: Any) -> None:
    if user_id not in _USERS:
        raise NotFoundError(f"user: '{user_id}' was not found")

    attrs = _USERS[user_id]
    if attribute_name not in attrs:
        raise NotFoundError(f"attribute: '{attribute_name}' was not found for user")

    attrs[attribute_name] = attribute_value


async def delete_user_attribute(user_id: ObjectId, attribute_name: str) -> None:
    if user_id not in _USERS:
        raise NotFoundError(f"user: '{user_id}' was not found")

    attrs = _USERS[user_id]
    if attribute_name not in attrs:
        raise NotFoundError(f"attribute: '{attribute_name}' was not found for user")

    del attrs[attribute_name]


async def create_policy(conditions: List[Dict[str, Any]]) -> ObjectId:
    policy_id = ObjectId()
    _POLICIES[policy_id] = conditions
    return policy_id


def get_policy(policy_id: ObjectId) -> Dict[str, Any]:
    if policy_id not in _POLICIES:
        raise NotFoundError(f"policy: '{policy_id}' was not found")

    return {
        "policy_id": policy_id,
        "conditions": _POLICIES[policy_id].copy()
    }


async def override_policy_conditions(policy_id: ObjectId, conditions: List[Dict[str, Any]]) -> None:
    if policy_id not in _POLICIES:
        raise NotFoundError(f"policy: '{policy_id}' was not found")
    _POLICIES[policy_id] = conditions


async def create_resource(policy_ids: List[ObjectId]) -> ObjectId:
    resource_id = ObjectId()
    _RESOURCES[resource_id] = policy_ids
    return resource_id


async def get_resource(resource_id: ObjectId) -> Dict[str, Any]:
    if resource_id not in _RESOURCES:
        raise NotFoundError(f"resource: '{resource_id}' was not found")

    return {
        "resource_id": resource_id,
        "policy_ids": _RESOURCES[resource_id].copy()
    }


async def override_resource_policy_ids(resource_id: ObjectId, policy_ids: List[ObjectId]) -> None:
    if resource_id not in _RESOURCES:
        raise NotFoundError(f"resource: '{resource_id}' was not found")
    _RESOURCES[resource_id] = policy_ids

