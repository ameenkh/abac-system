from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from bson import ObjectId

from api.common.cache_manager import conditions_cache
from api.common.configs import DB, USERS_COL, RESOURCES_COL
from api.common.exceptions import NotFoundError
from api.common.utils import apply, assert_query_param_existence

routes = web.RouteTableDef()


# executor = ProcessPoolExecutor(max_workers=2)
executor = ThreadPoolExecutor(max_workers=2)


# def task(policy_id: ObjectId, user_attributes: Dict[str, Any]) -> Tuple[ObjectId, bool]:
#     policy_conditions = (db.get_policy(policy_id))["conditions"]
#     for cond in policy_conditions:
#         if not apply(cond, user_attributes):
#             return policy_id, False
#     else:
#         # all conditions are met
#         return policy_id, True


@routes.get('/is_authorized')
async def is_authorized(request: web.Request):
    user_id = assert_query_param_existence(request, "user_id")
    resource_id = assert_query_param_existence(request, "resource_id")

    user_id = ObjectId(user_id)
    resource_id = ObjectId(resource_id)

    # Get User attributes from DB
    # Decided here not to save the users data in Redis cache because there will be about 10 changes per second,
    # and it won't be efficient to clear & populate the cache this many times per second, it just will be overhead.
    # so the system can tolerate querying by _id (its indexed) and there is only about 1000 users in the database
    user_doc = request.app["mongodb"][DB][USERS_COL].find_one({"_id": user_id})
    if not user_doc:
        raise NotFoundError(f"user: '{user_id}' was not found")
    user_attributes = user_doc["attributes"]

    # Get Resource policies ids from DB
    resource_doc = request.app["mongodb"][DB][RESOURCES_COL].find_one({"_id": resource_id})
    if not resource_doc:
        raise NotFoundError(f"resource: '{resource_id}' was not found")
    policy_ids = resource_doc["policy_ids"]

    for policy_id in policy_ids:
        # Get the policy conditions from cache
        for cond in conditions_cache.get(request, policy_id):
            if not apply(cond, user_attributes):
                break
        else:
            # all conditions are met
            is_auth = True
            break
    else:
        is_auth = False


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
