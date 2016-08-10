#!/usr/bin/env python
# I split this function here because copying adjoint source files
# takes some time. So you may just want to copy it once.

from __future__ import print_function, division
import os
from seisforward.copy_adjoint_source import copy_adjoint_source
from seisforward.utils import load_config, read_txt_into_list


if __name__ == "__main__":
    config_file = "config.yml"
    eventlist_file = "_XEVENTID.all"

    if not os.path.exists(config_file):
        raise ValueError("Missing config file: %s" % config_file)

    if not os.path.exists(eventlist_file):
        raise ValueError("Missing eventlist file: %s" % eventlist_file)

    events = read_txt_into_list(eventlist_file)
    config = load_config(config_file)
    adjointdir = config["data_info"]["adjointfolder"]
    archivedir = os.path.join(config["data_info"]["runbase"], "archive")

    copy_adjoint_source(events, adjointdir, archivedir)
