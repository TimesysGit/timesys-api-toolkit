# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import logging
import sys
from timesys import (
    core,
    utilities,
    vigiles,
)

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

try:
    __version__ = metadata.version(__package__)
except Exception:
    __version__ = '0.0.0'


logger = logging.getLogger(__name__)

# Call timesys.llapi.configure() to finish initializing
llapi = core.LLAPI()
