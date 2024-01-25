from aiohttp import web
from bson import ObjectId

from api.common import db
from api.common.models import ResourceSchema
from api.common.utils import assert_path_param_existence

routes = web.RouteTableDef()
schema = ResourceSchema()


@routes.post('/resources')
async def create_resource(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    json_body["policy_ids"] = [ObjectId(policy_id) for policy_id in json_body["policy_ids"]]
    [db.get_policy(policy_id) for policy_id in json_body["policy_ids"]]

    resource_id = await db.create_resource(json_body["policy_ids"])
    return web.json_response({"resource_id": str(resource_id)})


@routes.get('/resources/{resource_id}')
async def get_resource(request: web.Request):
    resource_id = assert_path_param_existence(request, "resource_id")

    data = await db.get_resource(ObjectId(resource_id))
    data["resource_id"] = str(data["resource_id"])
    data["policy_ids"] = [str(pid) for pid in data["policy_ids"]]
    return web.json_response(data)


@routes.put('/resources/{resource_id}')
async def override_resource_policy_ids(request: web.Request):
    resource_id = assert_path_param_existence(request, "resource_id")

    json_body = await request.json(loads=schema.loads)
    json_body["policy_ids"] = [ObjectId(policy_id) for policy_id in json_body["policy_ids"]]
    [db.get_policy(policy_id) for policy_id in json_body["policy_ids"]]

    await db.override_resource_policy_ids(ObjectId(resource_id), json_body["policy_ids"])
    return web.json_response({"status": "updated"})

