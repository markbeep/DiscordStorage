from storage.abstract import AbstractMessageStorage
from typing import Any
import json


class JSONStorage(AbstractMessageStorage[Any]):
    id = "json"

    async def decode_content(self, content: list[str]) -> Any:
        return json.loads("".join(content))

    async def encode_content(self, content: Any) -> list[str]:
        txt = json.dumps(content, separators=(",", ":"))
        return [txt[i : i + 1900] for i in range(0, len(txt), 1900)]
