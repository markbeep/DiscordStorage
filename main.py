import os
from typing import cast
import discord
from dotenv import load_dotenv

from storage.abstract import MessagePair
from storage.root import RootStorage
from storage.setpixel import SetPixelStorage, SetPixel


cache = []


class StorageClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        assert self.application

        dm_channel = await self.application.owner.create_dm()

        root_content = RootStorage(self)

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

        if "pixel" not in storages:
            pixel_storage = SetPixelStorage(self)
            pair = await pixel_storage.init_chain(dm_channel.id)
            storages["pixel"] = pixel_storage
            await root_content.write_all(storages)

        pixel_storage = cast(SetPixelStorage, storages["pixel"])
        await pixel_storage.append_message([SetPixel(1, 2, "foo", "bar")])

        print(await pixel_storage.read_all())


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
