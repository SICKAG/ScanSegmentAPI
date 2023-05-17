#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
import os
import pytest

# Session fixtures which can be used by all unit tests.

@pytest.fixture(scope="session")
def sample_file():
    """
    Provides a basic wrapper to easily load sample files containing serialized data. Sample files must be placed inside
    'sample_files' directory without sub-directories.

    Usage:
        def my_test(sample_file):
            path_of_file = sample_file("sample.compact")
    """
    return lambda filename: os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_files", filename)
