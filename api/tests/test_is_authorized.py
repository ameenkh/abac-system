from typing import Any, Dict, List

from aiohttp import web
from bson import ObjectId

from api.common.cache_manager import ConditionsCacheLoader
from api.common.utils import decide_if_authorized

mocked_request = object()
age_policy = ObjectId()
age_and_is_manager_policy = ObjectId()
john_is_manager_policy = ObjectId()


class MockedConditionCache(ConditionsCacheLoader):

    def get(self, request: web.Request, policy_id: ObjectId) -> List[Dict[str, Any]]:
        if policy_id == age_policy:
            return [
                {
                    "attribute_name": "age",
                    "operator": ">",
                    "value": 30
                }
            ]
        elif policy_id == age_and_is_manager_policy:
            return [
                {
                    "attribute_name": "age",
                    "operator": "<",
                    "value": 50
                },
                {
                    "attribute_name": "is_manager",
                    "operator": "=",
                    "value": True
                }
            ]
        elif policy_id == john_is_manager_policy:
            return [
                {
                    "attribute_name": "is_manager",
                    "operator": "=",
                    "value": True
                },
                {
                    "attribute_name": "name",
                    "operator": "=",
                    "value": "John"
                },
            ]
        else:
            return []


mocked_conditions_cache = MockedConditionCache()


def test_decide_if_authorized():
    assert decide_if_authorized([age_policy], {"age": 31}, mocked_conditions_cache, mocked_request)
    assert decide_if_authorized([age_and_is_manager_policy], {"age": 31, "is_manager": True}, mocked_conditions_cache, mocked_request)
    assert decide_if_authorized([john_is_manager_policy], {"age": 31, "is_manager": True, "name": "John"}, mocked_conditions_cache, mocked_request)

    # one of the policies are true
    assert decide_if_authorized([age_policy, age_and_is_manager_policy], {"age": 51}, mocked_conditions_cache, mocked_request)

    # Condition attribute does not exist on user's attribute
    assert not decide_if_authorized([age_policy], {"name": "John"}, mocked_conditions_cache, mocked_request)