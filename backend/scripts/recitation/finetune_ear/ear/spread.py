"""Which few of many sorted files to read. Its own file so cloud.py, which runs on this computer without the
run's libraries, picks tlog's files exactly as sources.py picks the others."""


def evenly(files, want):  # about `want` of them, spread over the whole set rather than its start
    step = max(1, len(files) // want)
    return files[step // 2::step]
