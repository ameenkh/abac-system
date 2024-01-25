from aiohttp import web

from api.common.cache_manager import attributes_cache
from api.common.configs import ATTRIBUTES_COL, DB
from api.common.exceptions import NotFoundError
from api.common.models import AttributeSchema
from api.common.utils import assert_path_param_existence

routes = web.RouteTableDef()
schema = AttributeSchema()


@routes.get('/attributes/{attribute_name}')
async def get_attribute(request: web.Request):
    attribute_name = assert_path_param_existence(request, "attribute_name")
    doc = request.app["mongodb"][DB][ATTRIBUTES_COL].find_one({"_id": attribute_name})
    if not doc:
        raise NotFoundError(f"attribute: '{attribute_name}' was not found")
    return web.json_response(doc)


@routes.post('/attributes')
async def create_attribute(request: web.Request):
    json_body = await request.json(loads=schema.loads)

    attribute_name = json_body.pop("attribute_name")
    doc = {
        "_id": attribute_name,  # using the _id as unique index, since it's automatically created by mongo
        "attribute_type": json_body["attribute_type"]
    }
    request.app["mongodb"][DB][ATTRIBUTES_COL].insert_one(doc)  # So in case of duplicate _id it will throw pymongo.errors.DuplicateKeyError
    attributes_cache.invalidate(request)
    return web.json_response({attribute_name: json_body["attribute_type"]})
