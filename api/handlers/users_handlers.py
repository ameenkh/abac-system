from aiohttp import web
from bson import ObjectId

from api.common import db
from api.common.models import PatchUserAttributeSchema, UserSchema
from api.common.utils import assert_path_param_existence, validate_values_types

routes = web.RouteTableDef()
schema = UserSchema()
patch_user_attribute_schema = PatchUserAttributeSchema()


@routes.post('/users')
async def create_user(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    attrs_conf = [await db.get_attribute(k) for k in json_body["attributes"]]
    attrs_conf = {x["attribute_name"]: x["attribute_type"] for x in attrs_conf}
    validate_values_types(attrs_conf, json_body["attributes"])

    user_id = await db.create_user(json_body["attributes"])
    return web.json_response({"user_id": str(user_id)})


@routes.get('/users/{user_id}')
async def get_user(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")

    data = await db.get_user(ObjectId(user_id))
    data["user_id"] = str(data["user_id"])
    return web.json_response(data)


@routes.put('/users/{user_id}')
async def override_user_attributes(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")

    json_body = await request.json(loads=schema.loads)
    attrs_conf = [await db.get_attribute(k) for k in json_body["attributes"]]
    attrs_conf = {x["attribute_name"]: x["attribute_type"] for x in attrs_conf}
    validate_values_types(attrs_conf, json_body["attributes"])

    await db.override_user_attributes(ObjectId(user_id), json_body["attributes"])
    return web.json_response({"status": "updated"})


@routes.patch('/users/{user_id}/attributes/{attribute_name}')
async def patch_user_attribute(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")
    attribute_name = assert_path_param_existence(request, "attribute_name")

    json_body = await request.json(loads=patch_user_attribute_schema.loads)
    json_body["attributes"] = {
        attribute_name: json_body["attribute_value"]
    }
    attrs_conf = [await db.get_attribute(k) for k in json_body["attributes"]]
    attrs_conf = {x["attribute_name"]: x["attribute_type"] for x in attrs_conf}
    validate_values_types(attrs_conf, json_body["attributes"])

    await db.patch_user_attribute(ObjectId(user_id), attribute_name, json_body["attribute_value"])
    return web.json_response({"status": "updated"})


@routes.delete('/users/{user_id}/attributes/{attribute_name}')
async def delete_user_attribute(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")
    attribute_name = assert_path_param_existence(request, "attribute_name")

    await db.delete_user_attribute(ObjectId(user_id), attribute_name)
    return web.json_response({"status": "deleted"})
