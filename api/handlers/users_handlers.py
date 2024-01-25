from typing import Any, Dict

from aiohttp import web
from bson import ObjectId
from pymongo.results import InsertOneResult, UpdateResult

from api.common.configs import ATTRIBUTES_COL, DB, USERS_COL
from api.common.exceptions import NotFoundError
from api.common.models import PatchUserAttributeSchema, UserSchema
from api.common.utils import assert_path_param_existence, validate_values_types

routes = web.RouteTableDef()
schema = UserSchema()
patch_user_attribute_schema = PatchUserAttributeSchema()


def _validate_attributes(request, user_attributes: Dict[str, Any]) -> None:
    attrs_docs = request.app["mongodb"][DB][ATTRIBUTES_COL].find({
        "_id": {"$in": list(user_attributes.keys())}
    })
    attrs_docs = {d["_id"]: d["attribute_type"] for d in attrs_docs}
    validate_values_types(attrs_docs, user_attributes)


@routes.post('/users')
async def create_user(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    _validate_attributes(request, json_body["attributes"])
    doc = {
        "attributes": json_body["attributes"]
    }
    res: InsertOneResult = request.app["mongodb"][DB][USERS_COL].insert_one(doc)
    return web.json_response({"user_id": str(res.inserted_id)})


@routes.get('/users/{user_id}')
async def get_user(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")

    doc = request.app["mongodb"][DB][USERS_COL].find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise NotFoundError(f"user: '{user_id}' was not found")
    return web.json_response(schema.dump(doc))


@routes.put('/users/{user_id}')
async def override_user_attributes(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")
    json_body = await request.json(loads=schema.loads)
    _validate_attributes(request, json_body["attributes"])

    res: UpdateResult = request.app["mongodb"][DB][USERS_COL].update_one(
        filter={"_id": ObjectId(user_id)},
        update={
            "$set": {
                "attributes": json_body["attributes"]
            }
        }
    )

    return web.json_response({"user_id": user_id})


@routes.patch('/users/{user_id}/attributes/{attribute_name}')
async def patch_user_attribute(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")
    attribute_name = assert_path_param_existence(request, "attribute_name")

    json_body = await request.json(loads=patch_user_attribute_schema.loads)
    _validate_attributes(request, {attribute_name: json_body["attribute_value"]})

    res: UpdateResult = request.app["mongodb"][DB][USERS_COL].update_one(
        filter={"_id": ObjectId(user_id)},
        update={
            "$set": {
                f"attributes.{attribute_name}": json_body["attribute_value"]
            }
        }
    )
    return web.json_response({"user_id": user_id})


@routes.delete('/users/{user_id}/attributes/{attribute_name}')
async def delete_user_attribute(request: web.Request):
    user_id = assert_path_param_existence(request, "user_id")
    attribute_name = assert_path_param_existence(request, "attribute_name")

    res: UpdateResult = request.app["mongodb"][DB][USERS_COL].update_one(
        filter={"_id": ObjectId(user_id)},
        update={
            "$unset": {
                f"attributes.{attribute_name}": ""
            }
        }
    )
    return web.json_response({"user_id": user_id})
