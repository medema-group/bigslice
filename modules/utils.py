#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.utils

Utility functions and classes
"""


import os


def reversed_fp_iter(fp, buf_size=8192):
    """a generator that returns the lines of a file in reverse order
    ref: https://stackoverflow.com/a/23646049/8776239
    """
    segment = None  # holds possible incomplete segment at the beginning of the buffer
    offset = 0
    fp.seek(0, os.SEEK_END)
    file_size = remaining_size = fp.tell()
    while remaining_size > 0:
        offset = min(file_size, offset + buf_size)
        fp.seek(file_size - offset)
        buffer = fp.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines = buffer.splitlines(True)
        # the first line of the buffer is probably not a complete line so
        # we'll save it and append it to the last line of the next buffer
        # we read
        if segment is not None:
            # if the previous chunk starts right from the beginning of line
            # do not concat the segment to the last line of new chunk
            # instead, yield the segment first
            if buffer[-1] == '\n':
                # print 'buffer ends with newline'
                yield segment
            else:
                lines[-1] += segment
                # print 'enlarged last line to >{}<, len {}'.format(lines[-1], len(lines))
        segment = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]
    # Don't yield None if the file was empty
    if segment is not None:
        yield segment
