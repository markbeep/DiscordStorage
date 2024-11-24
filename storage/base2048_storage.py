import zlib
import base2048
from storage.abstract import AbstractMessageStorage


class Base2048Storage(AbstractMessageStorage[str]):
    id = "base2048"

    async def decode_content(self, content: str) -> str:
        fixed = "".join(content.splitlines())
        return zlib.decompress(base2048.decode(fixed)).decode()

    async def encode_content(self, content: str) -> list[str]:
        data = zlib.compress(content.encode())
        encoded = base2048.encode(data)
        chunked = [encoded[i : i + 1900] for i in range(0, len(encoded), 1900)]
        return chunked
