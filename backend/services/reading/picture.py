"""An uploaded picture checked, and made ready for each reader.

Tesseract reads dark letters on a light ground, so its copy is grey and a dark page (a phone's dark
mode) is turned light. A photo taken at a slant (a page tilted a few degrees on the desk) is
straightened first: Tesseract follows lines that run level, and on a 4 degree photo it read half the
words, on a 15 degree one none. Enlarging and turning are asked for only on a second try (services/reading):
enlarging normal type made it read worse, and both cost time a clear page should not pay. The
model's copy keeps its colour and is only made small enough to send, and only when it is sent.
"""
from __future__ import annotations

import io

from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

# A phone photo is about 12 million pixels; a picture of more is no page of text, and Pillow
# would hold all of it in memory to find out (four bytes a pixel, before any copy is made).
_MOST_PIXELS = 24_000_000
# What a page is sent as (the browser makes anything else a JPEG first). Pillow can open many
# more, each a parser this upload would reach: TIFF, PSD, EPS through Ghostscript.
_FORMATS = ("PNG", "JPEG", "WEBP")
# A picture under _SMALL on its long side may have small type, worth an enlarged second read; no copy is over _LARGE.
_SMALL, _LARGE = 1800, 4000
# How far a page may lean and still be found (more is a page held sideways: tesseract.upright's job),
# the side its lean is measured at, and the least lean worth straightening.
_LEAN, _MEASURED, _LEAST = 20, 600, 1.0
# The model's copy: the long side it sees, and the JPEG quality it is sent at.
_SENT, _QUALITY = 2000, 90


class NotAPicture(ValueError):
    """The upload is not a picture Pillow can open, or is far too large to be a page."""


class Prepared:
    """One upload, opened once and page-sized; each reader's copy made only when that reader asks."""

    def __init__(self, colour: Image.Image):
        self.colour = colour
        self._grey: Image.Image | None = None

    def grey(self, scale: int = 1, turn: int = 0) -> bytes:
        """Tesseract's copy, as BMP (a PNG took 0.8s to write; BMP 0.01s, and reads the same).

        `scale` enlarges it (small type reads better twice the size); `turn` rotates it by that many
        degrees, counter-clockwise, for a photo taken sideways with no record of it.
        """
        grey = self._level()
        if turn:
            grey = grey.rotate(turn, expand=True, fillcolor=255)
        if scale > 1:
            grey = grey.resize((grey.width * scale, grey.height * scale), Image.Resampling.LANCZOS)
        return _encoded(_fit(grey, _LARGE), "BMP")

    def _level(self) -> Image.Image:
        """Grey, dark letters on light, and straightened: made once, the same for every read of this upload."""
        if self._grey is None:
            grey = self.colour.convert("L")
            if ImageStat.Stat(grey).mean[0] < 128:  # mostly dark: light letters on a dark ground
                grey = ImageOps.invert(grey)
            lean = lean_of(grey)
            if lean:  # the corners it opens filled with the page's own ground: white ones round a grey page, and Tesseract read nothing
                ground = int(ImageStat.Stat(grey).median[0])
                grey = grey.rotate(lean, Image.Resampling.BICUBIC, expand=True, fillcolor=ground)
            self._grey = grey
        return self._grey

    def small(self) -> bool:
        """Small enough that its type may be too: worth a second read enlarged when the first is unsure."""
        return max(self.colour.size) < _SMALL

    def jpeg(self) -> bytes:
        """The vision model's copy: colour, at most _SENT on its long side."""
        return _encoded(_fit(self.colour, _SENT), "JPEG", quality=_QUALITY)


def lean_of(grey: Image.Image) -> float:
    """How many degrees to turn a grey page (dark letters, light ground), counter-clockwise, for its lines
    to run level; 0 when they already do, or it has no lines to go by.

    Its rows of ink are summed at each angle: turned level, rows of letters and the gaps between them
    alternate sharply; at a slant every row catches a bit of several lines and the sums blur. Whole
    degrees across the range, then quarter degrees about the best. About a third of a second.
    """
    small = grey.copy()
    small.thumbnail((_MEASURED, _MEASURED))
    ink = small.point(lambda v: 255 if v < 160 else 0)

    def sharpness(angle: float) -> int:
        turned = ink.rotate(angle, Image.Resampling.BILINEAR, expand=True, fillcolor=0)
        rows = turned.resize((1, turned.height), Image.Resampling.BOX).tobytes()
        return sum((a - b) ** 2 for a, b in zip(rows, rows[1:]))

    level = sharpness(0)
    if not level:
        return 0.0
    rough = max(range(-_LEAN, _LEAN + 1), key=sharpness)
    best = max((rough + step / 4 for step in range(-3, 4)), key=sharpness)
    return best if abs(best) >= _LEAST and sharpness(best) > 1.5 * level else 0.0


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
    return Prepared(_on_white(image))


def _on_white(image: Image.Image) -> Image.Image:
    """RGB, with any transparency laid on white: a clear background is a light page, not a black one.
    A 16-bit picture is brought to 8 bits by scale, not by clipping, which turned its grey edges white."""
    if image.mode.startswith("I"):
        image = image.point(lambda v: v / 257).convert("L")
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        ground = Image.new("RGBA", image.size, "white")
        return Image.alpha_composite(ground, image).convert("RGB")
    return image.convert("RGB")


def _fit(image: Image.Image, longest: int) -> Image.Image:
    if max(image.size) <= longest:
        return image
    image = image.copy()
    image.thumbnail((longest, longest), Image.Resampling.LANCZOS)
    return image


def _encoded(image: Image.Image, kind: str, **options) -> bytes:
    out = io.BytesIO()
    image.save(out, kind, **options)
    return out.getvalue()
