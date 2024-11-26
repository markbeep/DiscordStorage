from storage.abstract import AbstractMessageStorage


class StringStorage(AbstractMessageStorage[str]):
    id = "string"

    async def decode_content(self, content: list[str]) -> str:
        return "".join(content)

    async def encode_content(self, content: str) -> list[str]:
        return [content[i : i + 1900] for i in range(0, len(content), 1900)]
