from typing import Dict, List, Any

from aiohttp import web
from bson import ObjectId
from redis.commands.json.path import Path

from api.common.configs import ATTRIBUTES_COL, DB, POLICIES_COL
from api.common.exceptions import NotFoundError


# Since upon each update (policy/user attribute) we need to check if the attribute exists in the global list
# Then it's best to save it in cache, specially when we have many updates per second,
# also there are "only" 1000 attribute (str to str) so it's pretty small and redis can handle it well
class _AttributesCacheLoader:
    TTL_SECONDS = 60 * 15  # 15 minutes

    @staticmethod
    def build_key() -> str:
        return "Attributes"

    @staticmethod
    def load(request: web.Request) -> Dict[str, str]:
        attrs_docs = request.app["mongodb"][DB][ATTRIBUTES_COL].find({})
        attrs_docs = {d["_id"]: d["attribute_type"] for d in attrs_docs}
        return attrs_docs

    def get(self, request: web.Request) -> Dict[str, str]:
        key = self.build_key()
        res = request.app["redis"].hgetall(key)
        if not res:  # list are not in cache
            # load dict from database
            attrs_docs = self.load(request)
            # write to Redis
            request.app["redis"].hset(key, mapping=attrs_docs)
            # set expiration time
            request.app["redis"].expire(key, self.TTL_SECONDS)
            return attrs_docs
        else:
            return res

    def invalidate(self, request: web.Request) -> None:
        request.app["redis"].delete(self.build_key())


# Getting the policy conditions is also a crucial part of the is_authorized calculation,
# and since each policy has only 20 conditions, then it fits well in redis and will be lightweight
class _ConditionsCacheLoader:
    TTL_SECONDS = 60 * 15  # 15 minutes

    @staticmethod
    def build_key(policy_id: ObjectId) -> str:
        return f"Policies:{policy_id}"

    @staticmethod
    def load(request: web.Request, policy_id: ObjectId) -> List[Dict[str, Any]]:
        policy_doc = request.app["mongodb"][DB][POLICIES_COL].find_one({"_id": policy_id})
        if not policy_doc:
            raise NotFoundError(f"policy: '{policy_id}' was not found")
        return policy_doc["conditions"]

    def get(self, request: web.Request, policy_id: ObjectId) -> List[Dict[str, Any]]:
        key = self.build_key(policy_id)
        res = request.app["redis"].json().get(key)
        if not res:  # conditions are not in cache
            # load conditions from database
            conditions = self.load(request, policy_id)
            # write to Redis
            request.app["redis"].json().set(key, Path.root_path(), conditions)
            # set expiration time
            request.app["redis"].expire(key, self.TTL_SECONDS)
            return conditions
        else:
            return res

    def invalidate(self, request: web.Request, policy_id: ObjectId) -> None:
        request.app["redis"].delete(self.build_key(policy_id))


attributes_cache: _AttributesCacheLoader = _AttributesCacheLoader()
conditions_cache: _ConditionsCacheLoader = _ConditionsCacheLoader()
