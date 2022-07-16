Timesys LinuxLink API Toolkit
=============================

This project contains a Python package and a command-line tool for interacting with APIs for Timesys services such as `Vigiles <https://www.timesys.com/solutions/vigiles-vulnerability-management/>`_.


Requirements
============

Usage of the APIs requires a `Key file <https://linuxlink.timesys.com/docs/wiki/engineering/LinuxLink_Key_File>`_ for authentication. The key file contains the user's email address and API key.

For configuring the Vigiles subpackage to use specific Product or Folder locations, refer to the `Dashboard Config <https://linuxlink.timesys.com/docs/vigiles-vulnerability-monitoring-and-management-user-guide#Dashboard-config>`_ documentation. Dashboard Config files are downloaded from Product pages on the `Vigiles Dashboard <https://linuxlink.timesys.com/vigiles/>`_ and passed to the core LLAPI object's ``configure`` method. Product and Folder tokens may also be set directly on that object without a file.


Getting Started
===============

To use the package, you must first import the LLAPI object and configure it. Without calling ``timesys.llapi.configure()``, no User email or API key are configured for authentication.

.. code-block::

    >>> import timesys
    >>> timesys.llapi.configure(key_file_path='/home/user/timesys/linuxlink_key')
    >>>
    >>> # Or if using a Vigiles Dashboard Config file:
    >>> timesys.llapi.configure(key_file_path='/home/user/timesys/linuxlink_key', dashboard_config_path='/path/to/config')

Verify authentication and server availability:

.. code-block::

    >>> from timesys.utilities import heartbeat
    >>> heartbeat()
    {'ok': True}

If the heartbeat is ok, you are ready to use any of the toolkit's modules!


Additional Notes
================

Logging
-------

It is up to the user to specify any custom handlers or formats for the logger if desired. For example:

.. code-block::

    >>> import logging
    >>> import timesys
    >>>
    >>> my_handler = logging.StreamHandler()
    >>> my_handler.setLevel(logging.INFO)
    >>> formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    >>> my_handler.setFormatter(formatter)
    >>> timesys.logger.addHandler(my_handler)

If you only want to change the log level, such as to hide warnings, you can also configure it this way:

.. code-block::

    >>> timesys.llapi.configure(log_level='ERROR')


Authentication
--------------

If you are writing your own API client library, such as in another language, please pay special attention to the code in :doc:`timesys.core.llapi`. the `LLAPI` class has private methods for generating the HMAC auth token from the API key. If this is not done exactly the same way as the server computes it, the signatures will never match.

To test your implementation, you can configure this module in a "dry run" mode which will output the auth header as well as the intermediary message used to create it (the `hmac_msg` key). Your code should be generating the same message and using the same hashing method to result in the same token for the header.

.. code-block::

    >>> import timesys
    >>> timesys.llapi.configure(key_file_path='/path/to/linuxlink_key', dry_run=True)
    Dry Run mode is enabled. No requests will be made.
    >>> timesys.utilities.heartbeat()
    {'headers': {'X-Auth-Signature': b'<token here>'}, 'method': 'POST', 'url': 'https://linuxlink.timesys.com/api/v1/heartbeat', 'data': {'email': 'user@example.com'}, 'hmac_msg': b'POST/api/v1/heartbeatemail=user@example.com'}


.. toctree::
   :maxdepth: 4
   :caption: Package Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
