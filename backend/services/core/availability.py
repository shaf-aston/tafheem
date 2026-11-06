"""What a data file on this machine can be in, said as-is so the reader is told which of the three
situations they are in, never a guess that flatters the app."""

MISSING = "missing"   # no file here; it was never installed or built
BROKEN = "broken"     # a file is there but could not be read; something is wrong, say so
READY = "ready"       # loaded, and a miss really means the book has no entry
