# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import timesys


def get_products():
    """Get product info for all products available to the current user

    Returns
    -------
    list of dict
        List of product information dictionaries which contains keys:
            "name", "description", "token"
    """

    resource = "/api/v1/vigiles/products"
    return timesys.llapi.GET(resource)


def create_product(product_name, product_description=None):
    """Create a new product for the current user

    Parameters
    ----------
    product_name : str
        Name for the new product
    product_description : str, optional
        Description for the new product


    Returns
    -------
    dict
        name : str
            Name of product
        description : str
            Description of product
        token : str
            Token of the new product
    """

    if not product_name:
        raise Exception("product_name is required")

    resource = "/api/v1/vigiles/products"
    data = {"name": product_name}

    if product_description:
        data["desc"] = product_description

    return timesys.llapi.POST(resource, data_dict=data)


def get_product_info(product_token=None):
    """Get product information from a product_token

    If a token is passed, it will be used.
    If no token is passed, but a product_token is configured on the llapi object, it will be used.
    If neither are provided, an Exception will be raised.

    Parameters
    ----------
    product_token : str, optional
        Token of the product to retrieve info for

    Returns
    -------
    dict
        name
            Name of product
        description
            Description of product
        token
            Token for the product
        is_default
            True if product is default product for user, otherwise False
        created
            Date that the product was created
    """

    if product_token is None:
        product_token = timesys.llapi.product_token

    if not product_token:
        raise Exception('product_token is required either as a parameter or configured on the llapi object')

    resource = f"/api/v1/vigiles/products/{product_token}"
    return timesys.llapi.GET(resource)
