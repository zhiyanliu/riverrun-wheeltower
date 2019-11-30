#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

# both two will be injected by RiverRun - WheelTower, DON"T edit manually.
credentials_pkg_url = "<CREDENTIALS_PACKAGE_URL>"
greengrass_core_config_url = "<GREENGRASS_CORE_CONFIG_URL>"
greengrass_core_pkg_url = "https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.10.0/greengrass-linux-x86-64-1.10.0.tar.gz"

# step1, download asset

credentials_pkg_path = "/tmp/credentials.zip"
greengrass_core_config_path = "/tmp/config.json"
greengrass_pkg_path = "/tmp/greengrass-linux-x86-64-1.10.0.tar.gz"
greengrass_home_path = "/opt/greengrass"


# download greengrass core root CA, certificates and keys
rc = os.system("curl -o %s -fs '%s'" % (credentials_pkg_path, credentials_pkg_url))
if 0 != rc:
    sys.exit(rc)

# download greengrass core config
rc = os.system("curl -o %s -fs '%s'" % (greengrass_core_config_path, greengrass_core_config_url))
if 0 != rc:
    sys.exit(rc)

# download greengrass package
rc = os.system("curl -o %s -fs '%s'" % (greengrass_pkg_path, greengrass_core_pkg_url))
if 0 != rc:
    sys.exit(rc)

# step2, install asset

# un-package Greengrass core package
rc = os.system("tar zxf %s --no-same-owner -C /opt" % greengrass_pkg_path)
if 0 != rc:
    sys.exit(rc)

# copy device root CA, certificates and keys
rc = os.system("unzip -o %s -d %s/certs" % (credentials_pkg_path, greengrass_home_path))
if 0 != rc:
    sys.exit(rc)

# copy Greengreen core config
rc = os.system("cp %s %s/config" % (greengrass_core_config_path, greengrass_home_path))
if 0 != rc:
    sys.exit(rc)

# step3, launch Greengrass core daemon
rc = os.system("%s/ggc/core/greengrassd start" % greengrass_home_path)
if 0 != rc:
    sys.exit(rc)

sys.exit(0)
