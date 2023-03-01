# SPDX-FileCopyrightText: 2023 Timesys Corporation
# SPDX-License-Identifier: MIT

import timesys


def get_folders(group_token=None):
    """**Access to this route requires a Vigiles prime subscription..**

    Get all folders that are owned by the current user.

    If a group token is configured on the llapi object, only folders belonging
    to that group will be returned.

    Returns
    -------
    list of dict
        List of folder information dictionaries with keys:
            "folder_token", "folder_name", "folder_description", "creation_date", "group_token"
    """

    data = {}
    group_token = group_token or timesys.llapi.group_token
    if group_token:
        data["group_token"] = group_token

    resource = "/api/v1/vigiles/folders"
    return timesys.llapi.GET(resource, data_dict=data)
