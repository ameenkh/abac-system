from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Tuple

from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
from bson import ObjectId

from api.common import db
from api.common.utils import apply, make_error

routes = web.RouteTableDef()


# executor = ProcessPoolExecutor(max_workers=2)
executor = ThreadPoolExecutor(max_workers=2)


def task(policy_id: ObjectId, user_attributes: Dict[str, Any]) -> Tuple[ObjectId, bool]:
    db.print_all()
    policy_conditions = (db.get_policy(policy_id))["conditions"]
    for cond in policy_conditions:
        if not apply(cond, user_attributes):
            return policy_id, False
    else:
        # all conditions are met
        return policy_id, True


@routes.get('/is_authorized')
async def is_authorized(request: web.Request):
    user_id = request.rel_url.query.get("user_id")
    resource_id = request.rel_url.query.get("resource_id")
    if not (user_id and resource_id):
        return web.json_response(make_error("Missing required query params: user_id, resource_id"), status=HTTPBadRequest.status_code)

    user_id = ObjectId(user_id)
    resource_id = ObjectId(resource_id)

    user_attributes = (await db.get_user(user_id))["attributes"]
    resource = await db.get_resource(resource_id)

    # The idea here is to calculate the fulfillment of the resource in parallel and then save it to cache
    futures = [executor.submit(task, policy_id, user_attributes) for policy_id in resource["policy_ids"]]
    policies_results = {}
    for future in as_completed(futures):
        result = future.result()
        policies_results[result[0]] = result[1]

    print(f"{policies_results=}")
    is_auth = any(policies_results.values())

    # for policy_id in resource["policy_ids"]:
    #     policy_conditions = (await storage.get_policy(policy_id))["conditions"]
    #     for cond in policy_conditions:
    #         if not apply(cond, user_attributes):
    #             break
    #     else:
    #         # all conditions are met
    #         is_auth = True
    #         break
    # else:
    #     is_auth = False

    return web.json_response({"is_authorized": is_auth})
