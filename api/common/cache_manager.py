from typing import Dict

from aiohttp import web

from api.common.configs import ATTRIBUTES_COL, DB


class _AttributesCacheLoader:
    KEY = "Attributes"
    TTL_SECONDS = 60 * 15  # 15 minutes

    @staticmethod
    def load(request: web.Request) -> Dict[str, str]:
        attrs_docs = request.app["mongodb"][DB][ATTRIBUTES_COL].find({})
        attrs_docs = {d["_id"]: d["attribute_type"] for d in attrs_docs}
        return attrs_docs

    def get(self, request: web.Request) -> Dict[str, str]:
        res = request.app["redis"].hgetall(self.KEY)
        if not res:  # list are not in cache
            # load dict from database
            attrs_docs = self.load(request)
            # write to Redis
            request.app["redis"].hset(self.KEY, mapping=attrs_docs)
            # set expiration time
            request.app["redis"].expire(self.KEY, self.TTL_SECONDS)
            return attrs_docs
        else:
            return res

    def invalidate(self, request: web.Request) -> None:
        request.app["redis"].delete(self.KEY)


attributes_cache: _AttributesCacheLoader = _AttributesCacheLoader()


