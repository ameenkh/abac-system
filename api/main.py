import logging

import pymongo
from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from aiohttp.web_exceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotFound
from aiohttp.web_middlewares import middleware
from aiohttp_swagger import setup_swagger
from marshmallow import ValidationError

from api.common.configs import (
    MONGODB_HOST,
    REDIS_DB_NUM,
    REDIS_HOST,
    REDIS_PASS,
    REDIS_PORT,
    SERVER_PORT,
)
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


# Healthcheck route, called every 15 seconds
# It just pings Redis and MongoDB to check if its alive
@routes.get('/health-check', allow_head=False)
async def health_check(request: web.Request):
    """
    ---
    description: This end-point allow to test that service is up.
    tags:
    - Health check
    produces:
    - text/plain
    responses:
        "200":
            description: successful operation. Return "Health Check is OK" text
    """
    assert request.app["redis"].ping()
    assert request.app["mongodb"].admin.command("ping")["ok"] == 1
    return web.Response(text="Health Check is OK")


@routes.get('/favicon.ico')  # This is a dummy endpoint in order to ignore icon requests from browsers
async def favicon(request: web.Request):
    return web.Response()


@middleware
async def safe_execution_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    try:
        # This middleware is responsible for handling all errors in the server and to prevent crashes
        # Each error has its own handling and its own status code to be returned
        return await handler(request)
    except NotFoundError as e:
        return web.json_response(make_error(str(e)), status=HTTPNotFound.status_code)
    except ValidationError as e:
        return web.json_response(make_error(str(e)), status=HTTPBadRequest.status_code)
    except Exception as e:
        logger.exception(f"Error while handling {request=}")
        return web.json_response(make_error(str(e)), status=HTTPInternalServerError.status_code)


async def init_mongodb_connection(app):
    app['mongodb'] = pymongo.MongoClient(MONGODB_HOST)
    logger.info("MongoDB connection initialized")
    yield
    # will be closed when the server terminates
    app['mongodb'].close()
    logger.info("MongoDB connection closed")


async def init_redis_connection(app):
    app["redis"] = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_NUM,
        password=REDIS_PASS,
        decode_responses=True
    )
    logger.info("Redis connection initialized")
    yield
    # will be closed when the server terminates
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

    setup_swagger(app=app, ui_version=3)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _app = app_factory()
    web.run_app(_app, port=SERVER_PORT, access_log_format="%P %a %t %r %s %Tf")
