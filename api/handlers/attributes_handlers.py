from aiohttp import web

from api.common.cache_manager import attributes_cache
from api.common.configs import ATTRIBUTES_COL, DB
from api.common.exceptions import NotFoundError
from api.common.models import CreateAttributeSchema, GetAttributeSchema
from api.common.utils import assert_path_param_existence

routes = web.RouteTableDef()
get_schema = GetAttributeSchema()
post_schema = CreateAttributeSchema()


@routes.get('/attributes/{attribute_name}', allow_head=False)
async def get_attribute(request: web.Request):
    """
        ---
        description: return attribute details
        tags:
        - Attributes
        parameters:
        - in: path
          name: attribute_name
          schema:
            type: string
          required: true
        produces:
        - application/json
        responses:
            200:
                description: successful operation. Return attribute details
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                attribute_name:
                                    type: string
                                attribute_type:
                                    type: string
        """
    attribute_name = assert_path_param_existence(request, "attribute_name")
    doc = request.app["mongodb"][DB][ATTRIBUTES_COL].find_one({"_id": attribute_name})
    if not doc:
        raise NotFoundError(f"attribute: '{attribute_name}' was not found")
    return web.json_response(get_schema.dump(doc))


@routes.post('/attributes')
async def create_attribute(request: web.Request):
    """
    ---
    description: Create attribute.
    tags:
    - Attributes
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        attribute_name:
                            type: string
                        attribute_type:
                            type: string
                            enum: ["string", "boolean", "integer"]
    responses:
        200:
            description: successful operation.
            content:
                application/json:
                    schema:
                        type: object
    """
    json_body = await request.json(loads=post_schema.loads)

    attribute_name = json_body.pop("attribute_name")
    doc = {
        "_id": attribute_name,  # using the _id as unique index, since it's automatically created by mongo
        "attribute_type": json_body["attribute_type"]
    }
    request.app["mongodb"][DB][ATTRIBUTES_COL].insert_one(doc)  # So in case of duplicate _id it will throw pymongo.errors.DuplicateKeyError

    # After modifying the global attributes, the attribute's cache needs to be cleared
    attributes_cache.invalidate(request)
    return web.json_response({attribute_name: json_body["attribute_type"]})
