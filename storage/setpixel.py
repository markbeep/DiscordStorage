from storage.abstract import AbstractMessageStorage


from dataclasses import dataclass


@dataclass
class SetPixel:
    x: int
    y: int
    color: str
    bot_id: str


class SetPixelStorage(AbstractMessageStorage[list[SetPixel]]):
    id = "pixel"

    async def decode_content(self, content: str) -> list[SetPixel]:
        lines = content.splitlines()
        decoded: list[SetPixel] = []
        for line in lines:
            x, y, color, bot_id = line.split()
            decoded.append(SetPixel(int(x), int(y), color, bot_id))
        return decoded

    async def encode_content(self, content: list[SetPixel]) -> list[str]:
        return [
            f"{pixel.x} {pixel.y} {pixel.color} {pixel.bot_id}" for pixel in content
        ]
