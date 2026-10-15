"""Daleel's books: one adapter per kind of book, each turning it into quotable passages.

Open `quran.py` for the simplest one, or `library.py` and `openiti.py` for the shapes that serve
many books. Every adapter follows the `Source` shape in `services/daleel/model.py`.
`services/daleel/registry.py` lists which adapters run, so adding a book is one file here and
one line there; `roots.py` supplies a passage's roots.
"""
