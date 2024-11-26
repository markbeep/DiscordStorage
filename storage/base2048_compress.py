import zlib
import base2048


def base2024_decode(content: str) -> str:
    return zlib.decompress(base2048.decode(content)).decode()


def base2024_encode(content: str) -> str:
    data = zlib.compress(content.encode())
    return base2048.encode(data)
