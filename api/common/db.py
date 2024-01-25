from typing import Any, Dict, List

from bson import ObjectId

from api.common.configs import (
    ATTRIBUTES_COL,
    DB,
    POLICIES_COL,
    RESOURCES_COL,
    USERS_COL,
)
from api.common.exceptions import NotFoundError

_ATTRIBUTES: Dict[str, str] = {}
_USERS: Dict[ObjectId, Dict[str, Any]] = {}
_POLICIES: Dict[ObjectId, List[Dict[str, Any]]] = {}
_RESOURCES: Dict[ObjectId, List[ObjectId]] = {}


def print_all(app):
    print("**** Attributes ****\n")
    for doc in app["mongodb"][DB][ATTRIBUTES_COL].find():
        print(f"\t{doc=}")

    print("**** Users ****\n")
    for doc in app["mongodb"][DB][USERS_COL].find():
        print(f"\t{doc=}")

    print("**** Policies ****\n")
    for doc in app["mongodb"][DB][POLICIES_COL].find():
        print(f"\t{doc=}")

    print("**** Resources ****\n")
    for doc in app["mongodb"][DB][RESOURCES_COL].find():
        print(f"\t{doc=}")


async def get_user(user_id: ObjectId) -> Dict[str, Any]:
    if user_id not in _USERS:
        raise NotFoundError(f"user: '{user_id}' was not found")

    return {
        "user_id": user_id,
        "attributes": _USERS[user_id].copy()
    }

def get_policy(policy_id: ObjectId) -> Dict[str, Any]:
    if policy_id not in _POLICIES:
        raise NotFoundError(f"policy: '{policy_id}' was not found")

    return {
        "policy_id": policy_id,
        "conditions": _POLICIES[policy_id].copy()
    }

async def get_resource(resource_id: ObjectId) -> Dict[str, Any]:
    if resource_id not in _RESOURCES:
        raise NotFoundError(f"resource: '{resource_id}' was not found")

    return {
        "resource_id": resource_id,
        "policy_ids": _RESOURCES[resource_id].copy()
    }

