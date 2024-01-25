from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Tuple

from aiohttp import web
from bson import ObjectId

from api.common import db
from api.common.configs import DB, USERS_COL, RESOURCES_COL, POLICIES_COL
from api.common.exceptions import NotFoundError
from api.common.utils import apply, make_error, assert_query_param_existence

routes = web.RouteTableDef()


# executor = ProcessPoolExecutor(max_workers=2)
executor = ThreadPoolExecutor(max_workers=2)


def task(policy_id: ObjectId, user_attributes: Dict[str, Any]) -> Tuple[ObjectId, bool]:
    policy_conditions = (db.get_policy(policy_id))["conditions"]
    for cond in policy_conditions:
        if not apply(cond, user_attributes):
            return policy_id, False
    else:
        # all conditions are met
        return policy_id, True


@routes.get('/is_authorized')
async def is_authorized(request: web.Request):
    user_id = assert_query_param_existence(request, "user_id")
    resource_id = assert_query_param_existence(request, "resource_id")

    user_id = ObjectId(user_id)
    resource_id = ObjectId(resource_id)

    # Get User attributes from DB
    user_doc = request.app["mongodb"][DB][USERS_COL].find_one({"_id": user_id})
    if not user_doc:
        raise NotFoundError(f"user: '{user_id}' was not found")
    user_attributes = user_doc["attributes"]

    # Get Resource policies ids from DB
    resource_doc = request.app["mongodb"][DB][RESOURCES_COL].find_one({"_id": resource_id})
    if not resource_doc:
        raise NotFoundError(f"resource: '{resource_id}' was not found")
    policy_ids = resource_doc["policy_ids"]

    # Get Policies from DB
    policies_docs = request.app["mongodb"][DB][POLICIES_COL].find({"_id": {"$in": policy_ids}})

    policies_results = {}
    for policy_doc in policies_docs:
        for cond in policy_doc["conditions"]:
            if not apply(cond, user_attributes):
                policies_results[policy_doc["_id"]] = False
                break
        else:
            # all conditions are met
            policies_results[policy_doc["_id"]] = True

    is_auth = any(policies_results.values())


    # The idea here is to calculate the fulfillment of the resource in parallel and then save it to cache
    # futures = [executor.submit(task, policy_id, user_attributes) for policy_id in policy_ids]
    # policies_results = {}
    # for future in as_completed(futures):
    #     result = future.result()
    #     policies_results[result[0]] = result[1]
    #
    # print(f"{policies_results=}")
    # is_auth = any(policies_results.values())

    return web.json_response({"is_authorized": is_auth})
