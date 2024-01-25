

# API configs
SERVER_PORT = 9876


# MongoDB configs
DB = "abac-db"
MONGODB_HOST = f"mongodb://mongodb:27017/{DB}?retryWrites=true&w=majority"
ATTRIBUTES_COL = "attributes"
USERS_COL = "users"
POLICIES_COL = "policies"
RESOURCES_COL = "resources"


# Redis configs
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB_NUM = 1
REDIS_PASS = "1234"

