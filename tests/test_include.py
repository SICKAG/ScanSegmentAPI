#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#

from scansegmentapi import compact_stream_extractor
from scansegmentapi import compact
from scansegmentapi import decode_util
from scansegmentapi import msgpack_stream_extractor
from scansegmentapi import msgpack_util
from scansegmentapi import msgpack
from scansegmentapi import tcp_handler
from scansegmentapi import udp_handler


def test_include():
    # Dummy assert just to test whether the imports are working
    assert True
