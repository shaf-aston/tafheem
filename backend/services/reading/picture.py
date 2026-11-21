"""An uploaded picture checked, and made ready for each reader.

Tesseract reads dark letters on a light ground at a fair size, so its copy is grey, a dark page
(a phone's dark mode) is turned light, and small type is enlarged: a screenshot of a chat read
"مرحبايا أذ ؛ قل" as it came and "مرحبا يا أخي، هل" so tidied. The model's copy keeps its colour
and is only made small enough to send.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

# A phone photo is about 12 million pixels; a picture of more is no page of text, and Pillow
# would hold all of it in memory to find out (four bytes a pixel, before any copy is made).
_MOST_PIXELS = 24_000_000
# What a page is sent as (the browser makes anything else a JPEG first). Pillow can open many
# more, each a parser this upload would reach: TIFF, PSD, EPS through Ghostscript.
_FORMATS = ("PNG", "JPEG", "WEBP")
# Tesseract's copy: under _SMALL on its long side is enlarged twice over, and no copy is over _LARGE.
_SMALL, _LARGE = 1800, 4000
# The model's copy: the long side it sees, and the JPEG quality it is sent at.
_SENT, _QUALITY = 2000, 90


class NotAPicture(ValueError):
    """The upload is not a picture Pillow can open, or is far too large to be a page."""


@dataclass(frozen=True)
class Prepared:
    grey: bytes    # PNG for Tesseract
    colour: bytes  # JPEG for the vision model


def prepare(body: bytes) -> Prepared:
    try:
        image = Image.open(io.BytesIO(body), formats=_FORMATS)
        if image.width * image.height > _MOST_PIXELS:
            raise NotAPicture("too many pixels for a page")
        image.draft("RGB", (_LARGE, _LARGE))  # a big JPEG decoded at a half or a quarter: less memory, no loss here
        image = ImageOps.exif_transpose(image)  # a phone photo held sideways is stored sideways
        image.thumbnail((_LARGE, _LARGE), Image.Resampling.LANCZOS)  # no copy below is ever larger than this
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as exc:
        raise NotAPicture(str(exc)) from exc
    colour = _on_white(image)
    return Prepared(grey=_png(_for_tesseract(colour)), colour=_jpeg(_fit(colour, _SENT)))


def _on_white(image: Image.Image) -> Image.Image:
    """RGB, with any transparency laid on white: a clear background is a light page, not a black one."""
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        ground = Image.new("RGBA", image.size, "white")
        return Image.alpha_composite(ground, image).convert("RGB")
    return image.convert("RGB")


def _for_tesseract(colour: Image.Image) -> Image.Image:
    grey = colour.convert("L")
    if ImageStat.Stat(grey).mean[0] < 128:  # mostly dark: light letters on a dark ground
        grey = ImageOps.invert(grey)
    if max(grey.size) < _SMALL:
        grey = grey.resize((grey.width * 2, grey.height * 2), Image.Resampling.LANCZOS)
    return _fit(grey, _LARGE)


def _fit(image: Image.Image, longest: int) -> Image.Image:
    if max(image.size) <= longest:
        return image
    image = image.copy()
    image.thumbnail((longest, longest), Image.Resampling.LANCZOS)
    return image


def _png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def _jpeg(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, "JPEG", quality=_QUALITY)
    return out.getvalue()
