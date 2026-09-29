from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from plugins.database import db


class Bot(Client):
    def __init__(self):
        super().__init__(
            "synax_join_manager",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=50,
            sleep_threshold=10,
        )

    async def start(self):
        await super().start()
        await db.setup()
        me = await self.get_me()
        self.username = me.username or ""
        print(f"Synax Join Manager started: @{self.username}")

    async def stop(self, *args):
        await super().stop()
        print("Synax Join Manager stopped")


if __name__ == "__main__":
    Bot().run()
