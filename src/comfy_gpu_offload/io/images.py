"""Helpers for encoding/decoding images to/from base64 strings."""

import base64
import io

from PIL import Image


def image_to_base64(image: Image.Image, *, format: str = "PNG") -> str:
    """Encode a PIL image to a base64 string (no data URI prefix)."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def base64_to_image(data: str) -> Image.Image:
    """Decode a base64 string into a PIL Image."""
    raw = base64.b64decode(data)
    buffer = io.BytesIO(raw)
    image = Image.open(buffer)
    image.load()  # Force load before buffer goes out of scope.
    return image
