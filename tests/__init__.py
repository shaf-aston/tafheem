"""Makes `tests` a package of this project.

Without this file a library installed into site-packages that also ships a
top-level `tests` package wins the import, and `from tests.test_naming import
token` in test_syntax_tree.py reaches that library instead, stopping the whole
suite from being collected.
"""
