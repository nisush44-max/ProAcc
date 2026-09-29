from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_NAME, DB_URI


class Database:
    def __init__(self, uri: str, database_name: str):
        if not uri:
            raise RuntimeError("DB_URI is missing. Add a MongoDB connection string to your environment.")
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
        self.db = self.client[database_name]
        self.users = self.db.users
        self.chats = self.db.chats
        self.accepted = self.db.accepted_requests
        self.settings = self.db.settings

    async def setup(self):
        await self.users.create_index("id", unique=True)
        await self.chats.create_index("chat_id", unique=True)
        await self.accepted.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
        await self.settings.create_index("key", unique=True)

    async def add_user(self, user_id, name):
        await self.users.update_one(
            {"id": int(user_id)},
            {"$set": {"name": name or "User"}, "$setOnInsert": {"id": int(user_id), "session": None}},
            upsert=True,
        )

    async def is_user_exist(self, user_id):
        return await self.users.find_one({"id": int(user_id)}, {"_id": 1}) is not None

    async def total_users_count(self):
        return await self.users.count_documents({})

    async def get_all_users(self):
        return self.users.find({}, {"id": 1})

    async def delete_user(self, user_id):
        await self.users.delete_one({"id": int(user_id)})

    async def set_session(self, user_id, session):
        await self.users.update_one({"id": int(user_id)}, {"$set": {"session": session}}, upsert=True)

    async def get_session(self, user_id):
        row = await self.users.find_one({"id": int(user_id)}, {"session": 1})
        return row.get("session") if row else None

    async def record_accept(self, chat_id, title, user_id):
        chat_id = int(chat_id)
        user_id = int(user_id)
        result = await self.accepted.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$setOnInsert": {"chat_id": chat_id, "user_id": user_id, "title": title or str(chat_id)}},
            upsert=True,
        )
        await self.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title or str(chat_id)}, "$inc": {"accepted": 1 if result.upserted_id else 0}},
            upsert=True,
        )
        return bool(result.upserted_id)

    async def total_accepted(self):
        return await self.accepted.count_documents({})

    async def chat_count(self):
        return await self.chats.count_documents({})

    async def get_chats(self, limit=30):
        return await self.chats.find({}).sort("accepted", -1).to_list(length=limit)

    async def get_setting(self, key, default=None):
        row = await self.settings.find_one({"key": key})
        return row.get("value", default) if row else default

    async def set_setting(self, key, value):
        await self.settings.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)


db = Database(DB_URI, DB_NAME)
