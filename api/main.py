import logging

import pymongo
from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from aiohttp.web_exceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotFound
from aiohttp.web_middlewares import middleware
from marshmallow import ValidationError

from api.common.exceptions import NotFoundError
from api.common.utils import make_error
from api.handlers import (
    attributes_handlers,
    is_authorized_handler,
    policies_handlers,
    resources_handlers,
    users_handlers,
)
from redis import Redis

logger = logging.getLogger("main")
routes = web.RouteTableDef()


@routes.get('/health-check')
async def health_check(request: web.Request):
    assert request.app["redis"].ping()
    assert request.app["mongodb"].admin.command("ping")["ok"] == 1
    return web.Response(text="Health Check is OK")


@routes.get('/favicon.ico')  # This is a dummy enpoint in order to ignore icon requests from browsers
async def health_check(request: web.Request):
    return web.Response()


@middleware
async def safe_execution_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    try:
        # This middleware is responsible for handling all errors in the server and to prevent crashes
        return await handler(request)
    except NotFoundError as e:
        return web.json_response(make_error(str(e)), status=HTTPNotFound.status_code)
    except ValidationError as e:
        return web.json_response(make_error(str(e)), status=HTTPBadRequest.status_code)
    except Exception as e:
        logger.exception(f"Error while handling {request=}")
        return web.json_response(make_error(str(e)), status=HTTPInternalServerError.status_code)


async def init_mongodb_connection(app):
    app['mongodb'] = pymongo.MongoClient("mongodb://mongodb:27017/abac-db?retryWrites=true&w=majority")
    logger.info("MongoDB connection initialized")
    yield
    app['mongodb'].close()
    logger.info("MongoDB connection closed")


async def init_redis_connection(app):
    app['redis'] = Redis(
        host="redis",
        port=6379,
        db=1,
        password="1234",
        decode_responses=True
    )
    logger.info("Redis connection initialized")
    yield
    app['redis'].close()
    logger.info("Redis connection closed")


async def app_factory() -> Application:
    app = web.Application(middlewares=[safe_execution_middleware])
    app.cleanup_ctx.append(init_mongodb_connection)
    app.cleanup_ctx.append(init_redis_connection)
    app.add_routes(attributes_handlers.routes)
    app.add_routes(users_handlers.routes)
    app.add_routes(policies_handlers.routes)
    app.add_routes(resources_handlers.routes)
    app.add_routes(is_authorized_handler.routes)
    app.add_routes(routes)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _app = app_factory()
    web.run_app(_app, port=9876, access_log_format="%P %a %t %r %s %Tf")


# curl -d @curl-json/attribute.json localhost:8765/attributes