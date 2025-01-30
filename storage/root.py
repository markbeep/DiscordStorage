import asyncio
from storage.abstract import AbstractMessageStorage, MessagePair
from typing import Any, Coroutine

from storage.json_storage import JSONStorage
from storage.setpixel import SetPixelStorage
from storage.string_storage import StringStorage


class RootStorage(AbstractMessageStorage[dict[str, AbstractMessageStorage[Any]]]):
    id = "root"

    async def decode_content(
        self, content: list[str]
    ) -> dict[str, AbstractMessageStorage[Any]]:
        storage_contents: dict[str, AbstractMessageStorage[Any]] = {}
        coros: list[Coroutine[Any, Any, MessagePair]] = []
        for line in content:
            name, channel_id, message_id, content_type = line.split()
            for typ in content_types:
                if typ.id == content_type:
                    storage = typ(self.client, self.channel_list)
                    storage_contents[name] = storage
                    coros.append(
                        storage.load_chain(
                            MessagePair(
                                message_id=int(message_id), channel_id=int(channel_id)
                            )
                        )
                    )
                    break
            else:
                print(f"Unknown content type: {content_type}")

        await asyncio.gather(*coros)

        return storage_contents

    async def encode_content(
        self, content: dict[str, AbstractMessageStorage[Any]]
    ) -> list[str]:
        return [
            f"{name} {pair.channel_id} {pair.message_id} {storage.id}"
            for name, storage in content.items()
            for pair in storage.chain
        ]


content_types = [
    SetPixelStorage,
    StringStorage,
    RootStorage,
    JSONStorage,
]
