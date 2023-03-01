# SPDX-FileCopyrightText: 2023 Timesys Corporation
# SPDX-License-Identifier: MIT

import timesys


def get_groups():
    """Get group info for all groups available to the current user

    Returns
    -------
    list of dict containing
        name : str
            Group name
        description : str
            Group description
        token : str
            Group token
        group_type : str
            Group type (Group or Subgroup)
        organization_token : str
            Parent organization token
    """

    resource = "/api/v1/vigiles/groups"
    return timesys.llapi.GET(resource)


def create_group(group_name, group_description=None, group_token=None):
    """Create a new group for the current user

    Parameters
    ----------
    group_name : str
        Name for the new group
    group_description : str, optional
        Description for the new group
    group_token: str, optional
        If group to be created is a subgroup, provide group token of parent
        group


    Returns
    -------
    dict
        name : str
            Name of group
        description : str
            Description of group
        token : str
            Token of the new group
    """

    if not group_name:
        raise Exception("group_name is required")

    resource = "/api/v1/vigiles/groups"
    data = {"group_name": group_name}

    if group_description:
        data["description"] = group_description

    if group_token is None:
        group_token = timesys.llapi.group_token

    if group_token:
        data["group_token"] = group_token

    return timesys.llapi.POST(resource, data_dict=data)


def get_group_info(group_token=None, subgroups=False):
    """Get group information from a group_token

    If a token is passed, it will be used.
    If no token is passed, but a group_token is configured on the llapi object, it will be used.
    If neither are provided, an Exception will be raised.

    Parameters
    ----------
    group_token : str, optional
        Token of the group to retrieve info for
    subgroups: bool, optional
        Set this to True to include subgroup details, default is False

    Returns
    -------
    dict
        name : str
            Group name
        description : str
            Group description
        token : str
            Group token
        group_type : str
            Group type (Group or Subgroup)
        organization_token : str
            Parent organization token
        subgroups : dict
            Subgroup dict containing subgroup name and token
    """

    if group_token is None:
        group_token = timesys.llapi.group_token

    if not group_token:
        raise Exception('group_token is required either as a parameter or configured on the llapi object')

    resource = f"/api/v1/vigiles/groups/{group_token}"
    data = {"subgroups": subgroups}
    
    return timesys.llapi.GET(resource, data_dict=data)
