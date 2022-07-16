# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import logging
logger = logging.getLogger(__name__)

from timesys import (
    core,
    utilities,
    vigiles,
)

# Call timesys.llapi.configure() to finish initializing
llapi = core.LLAPI()
