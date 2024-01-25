from aiohttp import web

from api.common import db
from api.common.models import AttributeSchema
from api.common.utils import assert_path_param_existence

routes = web.RouteTableDef()
schema = AttributeSchema()


@routes.get('/attributes/{attribute_name}')
async def get_attribute(request: web.Request):
    attribute_name = assert_path_param_existence(request, "attribute_name")
    data = await db.get_attribute(attribute_name)
    return web.json_response(data)


@routes.post('/attributes')
async def create_attribute(request: web.Request):
    json_body = await request.json(loads=schema.loads)
    await db.create_attribute(**json_body)
    return web.json_response({"status": "created"})
