#!/usr/bin/env python
"""
Set up directories for specfem simulation including
specfem related files(model files, binary files and etc).
Attention:
1) this script only setup the basic directory.
2) the copy of specfem(including model) might takes
    a little long time, depending on your model size.

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
    safe_makedir(runbase)

    subdirs = ["archive", "jobs", "specfem3d_globe"]
    for _dir in subdirs:
        safe_makedir(os.path.join(runbase, _dir))


def setup_forward_runbase(config):
    specfemdir = config["data_info"]["specfemdir"]
    runbase = config["runbase_info"]["runbase"]
    targetdir = os.path.join(runbase, "specfem3d_globe")
    easy_copy_specfem(specfemdir, targetdir)


def setup_adjoint_runbase(config):
    """
    Nothing needs to be done at this stage
    """
    pass


def setup_line_search_runbase(config):
    """
    Since line search will use different model files for
    different perturbation values, there is no need to copy
    the original mesh files here.
    """
    specfemdir = config["data_info"]["specfemdir"]
    runbase = config["runbase_info"]["runbase"]
    targetdir = os.path.join(runbase, "specfem3d_globe")
    easy_copy_specfem(specfemdir, targetdir, model_flag=False)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)
    validate_config(config)

    runbase = config["runbase_info"]["runbase"]
    create_runbase(runbase)

    stype = config["simulation"]["type"]
    if stype == "forward_simulation":
        setup_forward_runbase(config)
    elif stype == "adjoint_simulation":
        setup_adjoint_runbase(config)
    elif stype == "line_search":
        setup_line_search_runbase(config)
    else:
        raise NotImplementedError("Error: %s" % stype)


if __name__ == "__main__":
    main()
