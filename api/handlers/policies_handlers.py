from typing import Any, Dict, List

from aiohttp import web
from bson import ObjectId
from pymongo.results import InsertOneResult, UpdateResult

from api.common.configs import ATTRIBUTES_COL, DB, POLICIES_COL
from api.common.exceptions import NotFoundError
from api.common.models import PolicySchema
from api.common.utils import assert_path_param_existence, validate_conditions_types

routes = web.RouteTableDef()
schema = PolicySchema()


def _validate_conditions(request, conditions: List[Dict[str, Any]]) -> None:
    attrs_docs = request.app["mongodb"][DB][ATTRIBUTES_COL].find({
        "_id": {"$in": [cond["attribute_name"] for cond in conditions]}
    })
    attrs_docs = {d["_id"]: d["attribute_type"] for d in attrs_docs}
    validate_conditions_types(attrs_docs, conditions)


@routes.post('/policies')
async def create_policy(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    _validate_conditions(request, json_body["conditions"])

    doc = {
        "conditions": json_body["conditions"]
    }
    res: InsertOneResult = request.app["mongodb"][DB][POLICIES_COL].insert_one(doc)
    return web.json_response({"policy_id": str(res.inserted_id)})


@routes.get('/policies/{policy_id}')
async def get_policy(request: web.Request):
    policy_id = assert_path_param_existence(request, "policy_id")
    doc = request.app["mongodb"][DB][POLICIES_COL].find_one({"_id": ObjectId(policy_id)})
    if not doc:
        raise NotFoundError(f"policy: '{policy_id}' was not found")
    return web.json_response(schema.dump(doc))


@routes.put('/policies/{policy_id}')
async def override_policy_conditions(request: web.Request):
    policy_id = assert_path_param_existence(request, "policy_id")

    json_body = await request.json(loads=schema.loads)
    _validate_conditions(request, json_body["conditions"])

    res: UpdateResult = request.app["mongodb"][DB][POLICIES_COL].update_one(
        filter={"_id": ObjectId(policy_id)},
        update={
            "$set": {
                "conditions": json_body["conditions"]
            }
        }
    )
    return web.json_response({"policy_id": policy_id})

