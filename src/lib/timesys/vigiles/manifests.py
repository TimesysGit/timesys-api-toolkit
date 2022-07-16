# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import logging
import timesys

logger = logging.getLogger(__name__)


def get_manifests():
    """Get all manifests that are accessible by the current user

    Product or folder tokens can be configured to limit results, but only one
    may be provided. If configured on the llapi object, folder token takes
    precedence.

    Returns
    -------
    list of dict
        Each manifest in the returned list is a dictionary with the following keys:
            manifest_name
                Name of the manifest
            manifest_token
                Token representing the manifest
            product_token
                Token representing the Product which the manifest belongs to
            folder_token
                Token representing the Folder which the manifest belongs to
            upload_date
                Date the manifest was uploaded


    """

    resource = "/api/v1/vigiles/manifests"
    data = {}

    folder_token = timesys.llapi.folder_token
    product_token = timesys.llapi.product_token

    if folder_token is not None:
        data["folder_token"] = folder_token
    elif product_token is not None:
        data["product_token"] = product_token

    return timesys.llapi.GET(resource, data_dict=data)


def get_manifest_info(manifest_token, sbom_format=None):
    """Get manifest data along with metadata

    Parameters
    ----------
    sbom_format : str, optional
        If specified, the server will convert the manifest data to this format.
        Acceptable formats are:
            "spdx"
                Convert the manifest to SPDX format before returning it

    Returns
    -------
    dict
        Result of the request with keys:
            manifest_token
                Token representing the manifest
            manifest_name
                Name of the manifest with the given token
            folder_token
                Token representing a Folder the manifest belongs to
            product_token
                Token representing a Product the manifest belongs to
            upload_date
                Date the manifest was uploaded
            manifest_data
                Contents of the manifest
                By default this is the same format as it was uploaded, unless
                converted due to the "sbom_format" parameter
    """

    if not manifest_token:
        raise Exception("manifest_token is required")

    data = {}
    if sbom_format is not None:
        data["sbom_format"] = sbom_format

    resource = f"/api/v1/vigiles/manifests/{manifest_token}"
    return timesys.llapi.GET(resource, data_dict=data)


def get_manifest_file(manifest_token, sbom_format=None):
    """Get manifest data as a file

    Response does not include other metadata such as product/folder tokens.

    Parameters
    ----------
    sbom_format : str, optional
        If specified, the server will convert the manifest data to the specified format.
        Acceptable formats are:
            "spdx"
                Convert the manifest to SPDX format before returning it

    Returns
    -------
    bytes
        The raw manifest file bytes
    """

    if not manifest_token:
        raise Exception("manifest_token is required")

    resource = f"/api/v1/vigiles/manifests/{manifest_token}"
    data = {'send_file': True}
    if sbom_format:
        data["sbom_format"] = sbom_format
    return timesys.llapi.GET(resource, data_dict=data, json=False)


def upload_manifest(manifest, kernel_config=None, uboot_config=None, manifest_name=None, subfolder_name=None, filter_results=False, extra_fields=None, upload_only=False):
    """Upload and scan (optionally) a manifest

    If a product_token is configured on the llapi object, it will be used as the upload location.
    Otherwise, the default is "Private Workspace."

    If both a product_token and folder_token are configured on the llapi object, the folder will
    be the upload location.

    A subfolder name can optionally be supplied in order to upload to or create a folder under the
    configured product and folder. This will then be the upload target for the given manifest.
    This is not supported for "Private Workspace".

    Parameters
    ----------
    manifest : str
        String of manifest data to upload
    kernel_config : str, optional
        Kernel config data used to filter out CVEs which are irrelevant to the built kernel
    uboot_config : str, optional
        Uboot config data used to filter out CVEs which are irrelevant to the built bootloader
    manifest_name : str, optional
        Name to give the new manifest. If not provided, one will be generated and returned.
    subfolder_name : str, optional
        If given, a new folder will be created with this name under the configured product or folder,
        and the manifest will be uploaded to this new folder. If the subfolder already exists, it will be uploaded there.
        Not supported for "Private Workspace" Product.
    filter_results : bool
        True to apply all configured filters to scan results, False to apply only kernel and uboot config filters.
        Default: False
        Note: These filters are configured through the Vigiles web interface.
    extra_fields : list of str, optional
        Optionally extend CVE data included in report with any of the following fields:
            "assigner", "description", "impact", "modified", "problem_types", "published", "references"
    upload_only : bool
        If true, do not generate an initial CVE report for the uploaded manifest
        Default: False

    Returns
    -------
    dict
        Results of scan with keys:

        manifest_token
            Token of the manifest which was scanned
        product_token
            Token of the product that the manifest belongs to
        folder_token
            Token of the folder that the manifest belongs to
        cves : list of dict
            list of dictionaries containing information about CVEs found in the scan, also referred to as the "report."
        counts : dict
            Dictionary containing CVE counts with keys:
                "fixed", "kernel", "toolchain", "unapplied", "unfixed", "upgradable", "whitelisted"
        date
            Date the scan was performed
        report_path
            URL where the report can be viewed on the web.
            The report token may also be split from the end of this string.
        exported_manifest
            The manifest data in SPDX format
    """

    if not manifest:
        raise Exception('manifest data is required')

    resource = "/api/v1/vigiles/manifests"

    data = {
        "manifest": manifest,
        "filter_results": filter_results,
        "upload_only": upload_only,
    }

    if kernel_config is not None:
        data["kernel_config"] = kernel_config

    if manifest_name is not None:
        data["manifest_name"] = manifest_name

    if uboot_config is not None:
        data["uboot_config"] = uboot_config

    if subfolder_name is not None:
        data["subfolder_name"] = subfolder_name

    if extra_fields is not None:
        if not isinstance(extra_fields, list) or not all(isinstance(i, str) for i in extra_fields):
            raise Exception("Parameter 'extra_fields' must be a list of strings") from None
        data["with_field"] = extra_fields  # will be split into repeated params

    product_token = timesys.llapi.product_token
    folder_token = timesys.llapi.folder_token
    if folder_token:
        data["folder_token"] = folder_token
    if product_token:
        data["product_token"] = product_token
    else:
        logger.warning('No product token is configured. Upload target will be "Private Workspace"')

    if not product_token and (folder_token or subfolder_name):
        logger.warning('"Private Workspace" does not support folders. Since a product token is not configured, the folder_token and subfolder_name arguments will be ignored.')

    return timesys.llapi.POST(resource, data)


def rescan_manifest(manifest_token, rescan_only=False, filter_results=False, extra_fields=None):
    """Generate a new report for the given manifest_token

    Parameters
    ---------
    manifest_token : str
        Token for the manifest to rescan
    rescan_only : bool
        If True, rescan the manifest but not return the report data
        Default: False
    filter_results : bool
        Apply all filters to report if True, else only config filters if available.
        Default: False
    extra_fields : list of str, optional
        Optionally extend CVE data included in report with any of the following fields:
            "assigner", "description", "impact", "modified", "problem_types", "published", "references"

    Returns
    -------
    dict
        Results of scan with keys:

        manifest_token
            Token of the manifest which was scanned
        product_token
            Token of the product that the manifest belongs to
        folder_token
            Token of the folder that the manifest belongs to
        cves : list of dict
            list of dictionaries containing information about CVEs found in the scan, also referred to as the "report."
        counts : dict
            Dictionary containing CVE counts with keys:
                "fixed", "kernel", "toolchain", "unapplied", "unfixed", "upgradable", "whitelisted"
        date
            Date the scan was performed
        report_path
            URL where the report can be viewed on the web.
            The report token may also be split from the end of this string.
        exported_manifest
            The manifest data in SPDX format
    """
    if not manifest_token:
        raise Exception('manifest_token is required')

    resource = f"/api/v1/vigiles/manifests/{manifest_token}/reports"
    data = {
        "manifest": manifest_token,
        "rescan_only": rescan_only,
        "filtered": filter_results,
    }

    if extra_fields is not None:
        if not isinstance(extra_fields, list) or not all(isinstance(i, str) for i in extra_fields):
            raise Exception("Parameter 'extra_fields' must be a list of strings") from None
        data["with_field"] = extra_fields  # will be split into repeated params

    return timesys.llapi.POST(resource, data)


def delete_manifest(manifest_token, confirmed=False):
    """Delete a manifest with the given token

    This action can not be undone. It requires passing True for the
    'confirmed' keyword parameter to prevent accidental use.

    Parameters
    ---------
    manifest_token : str
        Token of the manifest to be deleted

    Returns
    -------
    dict
        success : bool
            True or False depending on result of operation
        message : str
            Reason when "success" is False. May refer to additional keys in response.

    Notes
    -----
    This action can not be undone!
    """

    if not manifest_token:
        raise Exception("manifest_token is required")

    resource = f"/api/v1/vigiles/manifests/{manifest_token}"
    data = {"confirmed": confirmed}
    return timesys.llapi.DELETE(resource, data_dict=data)


def get_report_tokens(manifest_token):
    """Get a list of report_tokens available for the given manifest_token

    Parameters
    ----------
    manifest_token : str
        Token of the manifest for which to retrieve a list of available reports

    Returns
    -------
    dict
        A dictionary with meta info about the requested manifest and a list of report info
        dictionaries, each of which contain the keys:
            "created_date", "report_token", "manifest_token", "manifest_version"
    """

    if not manifest_token:
        raise Exception("manifest_token is required")

    resource = f"/api/v1/vigiles/manifests/{manifest_token}/reports"
    return timesys.llapi.GET(resource)


def get_latest_report(manifest_token, filter_results=False, extra_fields=None):
    """Download the latest report for a manifest with the given token.

    Parameters
    ----------
    manifest_token : str
        Token of the manifest for which to fetch the latest report
    filter_results : bool
        apply all filters to report if True, else only config filters.
        Default: False
    extra_fields : list of str, optional
        Optionally extend CVE data included in report with any of the following fields:
            "assigner", "description", "impact", "modified", "problem_types", "published", "references"

    Returns
    -------
    dict
        Results of scan with keys:

        manifest_token
            Token of the manifest which was scanned
        product_token
            Token of the product that the manifest belongs to
        folder_token
            Token of the folder that the manifest belongs to
        cves : list of dict
            list of dictionaries containing information about CVEs found in the scan, also referred to as the "report."
        counts : dict
            Dictionary containing CVE counts with keys:
                "fixed", "kernel", "toolchain", "unapplied", "unfixed", "upgradable", "whitelisted"
        date
            Date the scan was performed
        product_path
            URL where the product can be viewed on the web.
        report_path
            URL where the report can be viewed on the web.
            The report token may also be split from the end of this string.

    """

    if not manifest_token:
        raise Exception("manifest_token is required")

    data = {
        'filtered': filter_results,
    }

    if extra_fields is not None:
        if not isinstance(extra_fields, list) or not all(isinstance(i, str) for i in extra_fields):
            raise Exception("Parameter 'extra_fields' must be a list of strings") from None
        data["with_field"] = extra_fields  # will be split into repeated params

    resource = f"/api/v1/vigiles/manifests/{manifest_token}/reports/latest"
    return timesys.llapi.GET(resource, data_dict=data)
