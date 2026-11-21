from pymongo import MongoClient
from pymongo.collection import Collection

from app.settings import settings


def connect_mongo() -> MongoClient:
    return MongoClient(
        settings.mongo_url,
        uuidRepresentation="standard",
        tz_aware=True,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        timeoutMS=5000,
    )


def prepare_tickets(client: MongoClient) -> Collection:
    collection = client[settings.mongo_database]["tickets"]
    collection.create_index(
        [("account_id", 1), ("created_at", -1), ("_id", -1)],
        name="tickets_by_owner_and_date",
    )
    return collection
