from storage.abstract import AbstractMessageStorage


class StringStorage(AbstractMessageStorage[str]):
    id = "string"

    async def decode_content(self, content: str) -> str:
        return content

    async def encode_content(self, content: str) -> list[str]:
        return content.splitlines()
