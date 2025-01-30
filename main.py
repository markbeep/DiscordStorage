import os
from typing import Optional, cast
import discord
from dotenv import load_dotenv

from storage.abstract import MessagePair
from storage.json_storage import JSONStorage
from storage.root import RootStorage


channel_list: dict[int, Optional[discord.abc.Messageable]] = {}


class StorageClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        assert self.application

        dm_channel = await self.application.owner.create_dm()

        root_content = RootStorage(self, channel_list)

        root_message_id = os.getenv("ROOT_MESSAGE_ID")
        if root_message_id is None or root_message_id == "0":
            print("No root message id found")
            pair = await root_content.init_chain(dm_channel.id)
            print(
                f"======================\nROOT MESSAGE ID = {pair.message_id}\n======================"
            )
            print("Add this ID as ROOT_MESSAGE_ID in .env.\nExiting...")
            await self.close()
            return

        await root_content.load_chain(
            MessagePair(
                message_id=int(root_message_id),
                channel_id=dm_channel.id,
            )
        )

        storages = await root_content.read_all()

        # dict of all available dm channels and the user IDs they belong to
        if "channels" not in storages:
            channel_storage = JSONStorage(self, channel_list)
            pair = await channel_storage.init_chain(dm_channel.id)
            storages["channels"] = channel_storage
            await root_content.write_all(storages)

        channel_storage = cast(JSONStorage, storages["channels"])
        await channel_storage.write_all(["foo", {"aaaa": "bbbb"}])

        print(await channel_storage.read_all())


def main():
    load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True

    client = StorageClient(intents=intents)
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        raise ValueError("No token found in .env")
    client.run(token)


if __name__ == "__main__":
    main()
