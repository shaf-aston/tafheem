"""The pure core of sarf: a word as letters that know their job, and the
book's rules that reshape those letters. No file reading, no HTTP, no AI.

`services/conjugation.py` is the only caller. It fills a template from
`data/sarf/patterns.json`, hands the result here, and prints what comes back.
"""
