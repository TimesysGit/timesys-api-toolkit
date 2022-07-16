# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT

import timesys


def download_report(report_token, format=None, filter_results=False):
    """Get a CVE report as a file from the given report token

    Parameters
    ----------
    token : str
        The token of the CVE report to download

    format : str
        What file format to return from the following:
            "csv", "pdf", "pdfsummary", "xlsx"

    filter_results : bool
        True to apply all configured filters to scan results,
        False to apply only kernel and uboot config filters, if configs have been uploaded.
        Default: False

    Returns
    -------
    file data : bytes
        CVE Report data in bytes from the requested file type
    """

    valid_formats = ["csv", "pdf", "pdfsummary", "xlsx"]

    if not report_token:
        raise Exception("report_token is required")

    if format not in valid_formats:
        raise Exception("Invalid or missing 'format' arg. "
                        f"Acceptable values: {', '.join(valid_formats)}")

    resource = f"/api/v1/vigiles/reports/{report_token}"
    data = {
        "filtered": filter_results,
        "format": format,
    }
    result = timesys.llapi.GET(resource, data_dict=data, json=False)

    return result


def compare_reports(token_one, token_two, remove_whitelist=False, filter_results=False):
    """Get comparison between report token_one and report token_two

    Arguments
    ---------
    token_one : str
        Token of the first CVE report
    token_two : str
        Token of the second CVE report
    remove_whitelist : bool
        Remove whitelisted CVEs from the report if True
        Default: False
    filter_results : bool
        Apply all filters to report if True, else only kernel and uboot config filters if configs have been uploaded.
        Default: False

    Returns
    -------
    dict
        Results of comparison with keys:
            resolved
                List of CVEs resolved between the reports
            new
                List new CVEs between the reports
    """

    if not (token_one and token_two):
        raise Exception("Two CVE report token arguments are required for comparison")

    resource = "/api/v1/vigiles/reports/compare"
    data = {
        "token_one": token_one,
        "token_two": token_two,
        "remove_whitelist": remove_whitelist,
        "filtered": filter_results,
    }
    return timesys.llapi.GET(resource, data)
