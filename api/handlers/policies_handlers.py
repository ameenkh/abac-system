from aiohttp import web
from bson import ObjectId

from api.common import db
from api.common.models import PolicySchema
from api.common.utils import assert_path_param_existence, validate_conditions_types

routes = web.RouteTableDef()
schema = PolicySchema()


@routes.post('/policies')
async def create_policy(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    attrs_conf = [await db.get_attribute(cond["attribute_name"]) for cond in json_body["conditions"]]
    attrs_conf = {x["attribute_name"]: x["attribute_type"] for x in attrs_conf}
    validate_conditions_types(attrs_conf, json_body["conditions"])

    policy_id = await db.create_policy(json_body["conditions"])
    return web.json_response({"policy_id": str(policy_id)})


@routes.get('/policies/{policy_id}')
async def get_policy(request: web.Request):
    policy_id = assert_path_param_existence(request, "policy_id")

    data = db.get_policy(ObjectId(policy_id))
    data["policy_id"] = str(data["policy_id"])
    return web.json_response(data)


@routes.put('/policies/{policy_id}')
async def override_policy_conditions(request: web.Request):
    policy_id = assert_path_param_existence(request, "policy_id")

    json_body = await request.json(loads=schema.loads)
    attrs_conf = [await db.get_attribute(cond["attribute_name"]) for cond in json_body["conditions"]]
    attrs_conf = {x["attribute_name"]: x["attribute_type"] for x in attrs_conf}
    validate_conditions_types(attrs_conf, json_body["conditions"])

    await db.override_policy_conditions(ObjectId(policy_id), json_body["conditions"])
    return web.json_response({"status": "updated"})

