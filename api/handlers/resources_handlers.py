from typing import List

from aiohttp import web
from bson import ObjectId
from marshmallow import ValidationError
from pymongo.results import InsertOneResult, UpdateResult

from api.common.configs import DB, POLICIES_COL, RESOURCES_COL
from api.common.exceptions import NotFoundError
from api.common.models import ResourceSchema
from api.common.utils import assert_path_param_existence

routes = web.RouteTableDef()
schema = ResourceSchema()


# Check if policy ids exists in the DB
def _validate_policy_ids(request, policy_ids: List[ObjectId]) -> None:
    policies_count = request.app["mongodb"][DB][POLICIES_COL].count_documents({
        "_id": {"$in": policy_ids}
    })
    if policies_count != len(policy_ids):
        raise ValidationError("All Policy ids must exist in the database")


@routes.post('/resources')
async def create_resource(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    _validate_policy_ids(request, json_body["policy_ids"])

    doc = {
        "policy_ids": json_body["policy_ids"]
    }
    res: InsertOneResult = request.app["mongodb"][DB][RESOURCES_COL].insert_one(doc)
    return web.json_response({"resource_id": str(res.inserted_id)})


@routes.get('/resources/{resource_id}')
async def get_resource(request: web.Request):
    resource_id = assert_path_param_existence(request, "resource_id")

    doc = request.app["mongodb"][DB][RESOURCES_COL].find_one({"_id": ObjectId(resource_id)})
    if not doc:
        raise NotFoundError(f"resource: '{resource_id}' was not found")

    return web.json_response(schema.dump(doc))


@routes.put('/resources/{resource_id}')
async def override_resource_policy_ids(request: web.Request):
    resource_id = assert_path_param_existence(request, "resource_id")

    json_body = await request.json(loads=schema.loads)
    _validate_policy_ids(request, json_body["policy_ids"])

    res: UpdateResult = request.app["mongodb"][DB][RESOURCES_COL].update_one(
        filter={"_id": ObjectId(resource_id)},
        update={
            "$set": {
                "policy_ids": json_body["policy_ids"]
            }
        }
    )

    return web.json_response({"resource_id": resource_id})

