#!/usr/bin/env python
"""
Set up directories for specfem simulation including
specfem related files(model files, binary files and etc).
Attention: this script only setup the basic directory
Developer: Wenjie Lei
-------------------
Directory structure:
  $runbase/
    archive/           # archive directory to store output data
    jobs/              # directory of job scripts
    specfem3d_globe/   # specfem directory(job running directory)
"""
from __future__ import print_function, division, absolute_import
import os
import argparse
from seisforward.utils import safe_makedir
from seisforward.io import load_config
from seisforward.validate_config import validate_config
from seisforward.easy_copy_specfem import easy_copy_specfem


def create_runbase(runbase):
    print("*" * 30 + "\nCreate runbase at dir: %s" % runbase)
    if not os.path.exists(runbase):
        os.makedirs(runbase)

    subdirs = ["archive", "jobs", "specfem3d_globe"]

    for _dir in subdirs:
        safe_makedir(os.path.join(runbase, _dir))


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)
    validate_config(config)

    runbase = config["runbase"]
    create_runbase(runbase)

    specfemdir = config["data_info"]["specfemdir"]
    targetdir = os.path.join(runbase, "specfem3d_globe")
    easy_copy_specfem(specfemdir, targetdir)


if __name__ == "__main__":
    main()
