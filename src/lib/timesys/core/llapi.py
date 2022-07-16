# SPDX-FileCopyrightText: 2022 Timesys Corporation
# SPDX-License-Identifier: MIT
import base64
from collections.abc import Sequence
import hashlib
import hmac
import json
import requests
import urllib.parse
import urllib3
import warnings

import logging

class LLAPI:
    """Interface for configuration and LinuxLink communication

    The "timesys" package holds an instance of this class which is shared by all
    subpackages and modules. It is instantiated automatically but is not ready for
    use until it is configured with a LinuxLink API Key, user email, and base
    URL at a minimum. The email and key are usually specified by a path to a
    downloaded Keyfile.

    Typical use would not be creating your own instance of this class, but instead
    calling the "configure" method on the existing, shared timesys.llapi object.
    The "configure" method takes the same parameters as the class "__init__".


    Parameters
    ----------
    key_file_path : str, optional
        Path to LinuxLink API Keyfile which contains the user's email and key.
        These values are required for authentication and must be configured
        before use.
    dashboard_config_path : str, optional
        Path to Dashboard Config file which may contain a Product or Folder token.
        Once configured, operations which can be limited to certain Products
        or Folders will use these values.
    url : str, optional
        The base URL for API communication. Default is https://linuxlink.timesys.com
    verify_cert : bool or str
        If False, insecure requests are enabled. Certificates will not be verified.
        May be set to a string containing the path to a CA_BUNDLE.
        Default is True.
    dry_run : bool
        If True, no requests will be sent to the server. Instead, details about the request are returned, including the parameters, headers, and intermediate message used to generate the HMAC authentication signature.
        This is intended to be useful as a reference when implementing a custom interface as well as for debugging requests.
        Default is False.
    log_level : str or int
        Specify the package's default log level.
        Default is "WARNING"
    """

    logger = logging.getLogger(__name__).getChild(__qualname__)

    @staticmethod
    def parse_keyfile(key_file_path):
        try:
            with open(key_file_path, "r") as key_file:
                key_info = json.load(key_file)
        except Exception as e:
            raise Exception("Unable to read key file: %s\n%s" % (key_file_path, e)) from None

        try:
            email = key_info["email"].strip()
            key = key_info["key"].strip().encode('utf-8')
        except Exception as e:
            raise Exception("Invalid or missing data in key file") from None

        return (email, key)

    @staticmethod
    def parse_dashboard_config(dashboard_config_path):
        try:
            with open(dashboard_config_path, "r") as dashboard_config:
                dashboard_config_info = json.load(dashboard_config)
        except Exception as e:
            raise Exception(f"Unable to read dashboard config: {dashboard_config_path}: {e}") from None

        try:
            product = dashboard_config_info["product"].strip()
        except Exception as e:
            raise Exception(f"Invalid or missing data in dashboard config: {e}") from None

        if "folder" in dashboard_config_info:
            folder = dashboard_config_info["folder"].strip()
        else:
            folder = None

        return {
            "product_token": product,
            "folder_token": folder,
        }

    def __init__(self, key_file_path=None, dashboard_config_path=None, url='https://linuxlink.timesys.com', verify_cert=True, dry_run=False, log_level='WARNING'):
        self.log_level = log_level
        self.email = None
        self.key = None
        self.url = None
        self.product_token = None
        self.folder_token = None
        self.verify_cert = None  # Note: unconfigured is the same as True
        self.dry_run = None

        self.configure(key_file_path=key_file_path, dashboard_config_path=dashboard_config_path, url=url, verify_cert=verify_cert, dry_run=dry_run, log_level=log_level)

    @property
    def current_config(self):
        return {
            "email": self.email,
            "key": self.key,
            "url": self.url,
            "product_token": self.product_token,
            "folder_token": self.folder_token,
            "verify_cert": self.verify_cert,
            "dry_run": self.dry_run,
            "log_level": self.log_level,
        }

    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, level):
        self._log_level = level
        self.logger.setLevel(self.log_level)

    @property
    def dry_run(self):
        return self._dry_run

    @dry_run.setter
    def dry_run(self, is_enabled):
        self._dry_run = is_enabled
        if is_enabled:
            self.logger.warning("Dry Run mode is enabled. No requests will be made.")

    @property
    def verify_cert(self):
        return self._verify_cert

    @verify_cert.setter
    def verify_cert(self, setting):
        self._verify_cert = setting
        if self.verify_cert is False:
            self.logger.warning('Insecure requests are enabled. Certificates will not be verified.')

    def _make_msg(self, method, resource, data):
        def sort_sequences(obj):
            # String values are Sequences but should not be sorted
            if isinstance(obj, str) or not isinstance(obj, Sequence):
                return obj
            return sorted(obj)

        args = sorted((k, sort_sequences(v)) for k, v in data.items())
        args = urllib.parse.unquote_plus(urllib.parse.urlencode(args, doseq=True))
        msg = "".join([method, resource, args])
        return msg.encode("utf-8")

    def _create_hmac(self, msg):
        sig = hmac.digest(self.key, msg, hashlib.sha256)
        return base64.b64encode(sig)

    def _prepare_request(self, method, resource, data_dict=None):
        if not self.configured:
            raise Exception('LLAPI object has not been configured.') from None

        if data_dict is None:
            data_dict = {}

        data_dict['email'] = self.email
        url = f"{self.url}{resource}"
        msg = self._make_msg(method, resource, data_dict)

        request = {
            'headers': {
                'X-Auth-Signature': self._create_hmac(msg),
            },
            'method': method.upper(),
        }

        if method.upper() != "POST":
            args = urllib.parse.urlencode(sorted(data_dict.items()), doseq=True)
            request["url"] = f"{url}?{args}"
        else:
            request["url"] = url
            request["data"] = data_dict

        if self.dry_run:
            request["hmac_msg"] = msg

        return request

    def _do_api_call(self, request_dict, json_response):
        if not self.configured:
            raise Exception('LLAPI object is not configured properly') from None

        if self.dry_run:
            return request_dict

        try:
            method = request_dict.pop('method')
            url = request_dict.pop('url')
        except KeyError as e:
            raise Exception('_do_api_call: Missing required key: %s' % e.args[0]) from None

        try:
            # only filter the InsecureRequestWarning for our call, rather than globally
            if self.verify_cert is False:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
                    r = requests.request(method, url, verify=False, **request_dict)
            else:
                r = requests.request(method, url, verify=self.verify_cert, **request_dict)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                e = r.json()    # errors should be JSON responses too,
            except ValueError:  # but just incase HTML comes back..
                e = r.status_code
            raise Exception(f"LinuxLink server returned an error: {e}") from None
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection could not be made: {e}") from None
        except requests.exceptions.Timeout:
            raise Exception("Connection attempt timed out") from None
        except Exception:
            raise

        if not json_response:
            return r.content  # bytes, which may be text or binary file content
        else:
            try:
                json_data = r.json()
            except Exception as e:
                raise Exception(f"_do_api_call: error parsing JSON response: {e}") from None
        return json_data

    def configure(self, key_file_path=None, dashboard_config_path=None, url=None, verify_cert=None, dry_run=None, log_level=None):
        if key_file_path:
            self.email, self.key = self.parse_keyfile(key_file_path)

        if dashboard_config_path:
            dashboard_config = self.parse_dashboard_config(dashboard_config_path)
            self.product_token = dashboard_config.get('product_token')
            self.folder_token = dashboard_config.get('folder_token')

        if url is not None:
            self.url = url

        if dry_run is not None:
            self.dry_run = dry_run

        if verify_cert is not None:
            # note: default if _never_ configured is None, which Requests
            # ignores. None/True/<path_to_CA_BUNDLE> all attempt verification.
            # Only explicitly setting this to False skips it.
            self.verify_cert = verify_cert

        if log_level is not None:
            self.log_level = log_level

        # email/key/url are required, so consider it unconfigured without them.
        if None in [self.email, self.key, self.url]:
            self.configured = False
        else:
            self.configured = True

    def DELETE(self, resource, data_dict=None, json=True):
        request = self._prepare_request('DELETE', resource, data_dict=data_dict)
        return self._do_api_call(request, json)

    def GET(self, resource, data_dict=None, json=True):
        request = self._prepare_request('GET', resource, data_dict=data_dict)
        return self._do_api_call(request, json)

    def PATCH(self, resource, data_dict=None, json=True):
        request = self._prepare_request('PATCH', resource, data_dict=data_dict)
        return self._do_api_call(request, json)

    def POST(self, resource, data_dict=None, json=True):
        request = self._prepare_request('POST', resource, data_dict=data_dict)
        return self._do_api_call(request, json)

    def PUT(self, resource, data_dict=None, json=True):
        request = self._prepare_request('PUT', resource, data_dict=data_dict)
        return self._do_api_call(request, json)
