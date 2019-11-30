#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

# both two will be injected by RiverRun - WheelTower, DON"T edit manually.
credentials_pkg_url = "<CREDENTIALS_PACKAGE_URL>"
greengrass_core_config_url = "<GREENGRASS_CORE_CONFIG_URL>"

# step1, download asset

credentials_pkg_path = "/tmp/credentials.zip"
greengrass_core_config_path = "/tmp/config.json"
greengrass_home = "/opt/greengrass"

# download greengrass core root CA, certificates and keys
rc = os.system("curl -o %s -fs '%s'" % (credentials_pkg_path, credentials_pkg_url))
if 0 != rc:
    sys.exit(rc)

# download greengrass core config
rc = os.system("curl -o %s -fs '%s'" % (greengrass_core_config_path, greengrass_core_config_url))
if 0 != rc:
    sys.exit(rc)

# download greengrass package


# step2, install asset
