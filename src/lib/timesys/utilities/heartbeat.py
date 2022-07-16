# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import timesys


def heartbeat():
    """Verify that auth is working and the server is responding

    If successful, the server returns {'ok': True}. Otherwise
    an appropriate Exception will be raised.

    Returns
    -------
    dict
        ok : bool
            True if the server accepted the request and was able to respond
    """
    resource = "/api/v1/heartbeat"
    return timesys.llapi.POST(resource)
