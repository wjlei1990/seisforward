#!/usr/bin/env python
"""
Set up directories for the source inversion, Except
specfem related files. For those files, use copy_mesh.pbs file
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
from .utils import safe_makedir, load_config, validate_config


def create_runbase(runbase):
    print("Create runbase at dir: %s" % runbase)
    if not os.path.exists(runbase):
        os.makedirs(runbase)

    subdirs = ["archive", "jobs", "specfem3d_globe"]

    for _dir in subdirs:
        safe_makedir(os.path.join(runbase, _dir))

    # safe_makedir(specfemdir)
    # safe_makedir(os.path.join(specfemdir, "DATA"))
    # safe_makedir(os.path.join(specfemdir, "bin"))
    # safe_makedir(os.path.join(specfemdir, "OUTPUT_FILES"))
    # safe_makedir(os.path.join(specfemdir, "DATABASES_MPI"))

    print("="*20 + "\nPlease use easy_copy_specfem.py to copy specfem into "
          "\"$runbase/specfem3d_globe\". \n"
          "Usage: seisforward-easy_copy_specfem -c config.yaml")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)
    validate_config(config)

    runbase = config["data_info"]["runbase"]
    create_runbase(runbase)


if __name__ == "__main__":
    main()
