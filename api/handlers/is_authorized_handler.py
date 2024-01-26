from aiohttp import web
from bson import ObjectId

from api.common.cache_manager import conditions_cache
from api.common.configs import DB, RESOURCES_COL, USERS_COL
from api.common.exceptions import NotFoundError
from api.common.utils import assert_query_param_existence, decide_if_authorized

routes = web.RouteTableDef()


@routes.get('/is_authorized')
async def is_authorized(request: web.Request):
    user_id = assert_query_param_existence(request, "user_id")
    resource_id = assert_query_param_existence(request, "resource_id")

    user_id = ObjectId(user_id)
    resource_id = ObjectId(resource_id)

    # Get User attributes from DB
    # Decided here not to save the users data in Redis cache because there will be up to 10 changes per second,
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

    is_auth = decide_if_authorized(policy_ids, user_attributes, conditions_cache, request)
    return web.json_response({"is_authorized": is_auth})
