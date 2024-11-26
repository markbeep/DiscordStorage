from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from typing import Generic, TypeVar

import discord

from storage.base2048_compress import base2024_decode, base2024_encode


@dataclass
class MessagePair:
    message_id: int
    channel_id: int


T = TypeVar("T")


class AbstractMessageStorage(ABC, Generic[T]):
    id: str

    def __init__(self, client: discord.Client) -> None:
        self.client = client

        self.channels: dict[int, discord.abc.Messageable] = {}
        """channel cache"""

        self.chain: list[MessagePair] = []

    async def init_chain(self, channel_id: int) -> MessagePair:
        channel = await self.client.fetch_channel(channel_id)
        assert isinstance(channel, discord.abc.Messageable)
        self.channels[channel_id] = channel
        message = await channel.send("0 0")
        pair = MessagePair(message.id, channel_id)
        self.chain.append(pair)
        return pair

    async def load_chain(self, initial_message: MessagePair) -> MessagePair:
        def parse_ids(content: str) -> tuple[int, int]:
            channel_id, message_id = content[: content.find("\n")].split(" ")
            return int(channel_id), int(message_id)

        channel_id, message_id = initial_message.channel_id, initial_message.message_id
        self.chain = [initial_message]

        while channel_id != 0 and message_id != 0:
            # we only want to fetch a channel once
            channel = self.channels.get(channel_id)
            if channel is None:
                channel = await self.client.fetch_channel(channel_id)
                assert isinstance(channel, discord.abc.Messageable)
                self.channels[channel_id] = channel
            message = await channel.fetch_message(int(message_id))
            channel_id, message_id = parse_ids(message.content)
            if channel_id == 0 and message_id == 0:
                break
            self.chain.append(MessagePair(message_id, channel_id))

        return self.chain[0]

    @abstractmethod
    async def decode_content(self, content: list[str]) -> T:
        """
        Receives the content of the messages joined by newlines.
        """
        pass

    async def _read_message(self, pair: MessagePair) -> list[str]:
        channel = self.channels[pair.channel_id]
        message = await channel.fetch_message(pair.message_id)
        lines = message.content.splitlines()[1:]
        return [base2024_decode(x) for x in lines]

    async def read(self, index: int) -> T:
        pair = self.chain[index]
        return await self.decode_content(await self._read_message(pair))

    async def read_all(self) -> T:
        if len(self.chain) == 0:
            raise ValueError("Chain hasn't been loaded yet")

        contents = await asyncio.gather(
            *[self._read_message(pair) for pair in self.chain]
        )
        contents = [line for d2 in contents for line in d2]

        return await self.decode_content(contents)

    @abstractmethod
    async def encode_content(self, content: T) -> list[str]:
        """
        How content should be encoded as Discord messages. Each string in the list is
        allowed to be at most 1900 characters long. The strings will be joined by newlines,
        but if needed, it will be split into multiple messages.
        """
        pass

    def _create_messages(
        self, content: list[str], last_message_content: str = ""
    ) -> list[str]:
        messages: list[str] = []
        current_message = last_message_content
        while len(content) > 0:
            line = base2024_encode(content.pop(0))
            if len(current_message) + len(line) + 1 <= 1900:
                current_message += line + "\n"
            else:
                messages.append(current_message)
                current_message = line + "\n"

        messages.append(current_message)

        return messages

    async def append_message(self, obj: T, ignore_last_message: bool = False):
        """
        Appends data to the current chain.
        """
        content = await self.encode_content(obj)
        assert all(
            len(line) <= 1900 for line in content
        ), "Each line must be at most 1900 characters long"

        last_message = self.chain[-1]
        channel = self.channels[last_message.channel_id]
        last_message = await channel.fetch_message(last_message.message_id)
        last_message_content = last_message.content.splitlines()

        encoded_contents = self._create_messages(
            content,
            "\n".join(last_message_content[1:]) + "\n"
            if len(last_message_content) > 1 and not ignore_last_message
            else "",
        )

        prev_channel_id = 0
        prev_message_id = 0
        for i, body in enumerate(encoded_contents[::-1]):
            # send last message first to get the id
            message_content = f"{prev_channel_id} {prev_message_id}\n{body}"
            assert len(message_content) <= 2000, "Message content too long"

            if i == len(encoded_contents) - 1:
                # in the last iteration we edit the original message instead of creating a new one
                await last_message.edit(content=message_content)
            else:
                message = await channel.send(message_content)
                self.chain.append(
                    MessagePair(message_id=message.id, channel_id=message.channel.id)
                )
                prev_channel_id = message.channel.id
                prev_message_id = message.id

    async def write_all(self, obj: T):
        """
        Creates a completely new chain with the contents.
        The start of the chain is the same message ID as before.
        """
        self.chain = self.chain[:1]
        await self.append_message(obj, True)
