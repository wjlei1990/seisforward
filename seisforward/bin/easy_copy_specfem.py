#!/usr/bin/env python
# ##########################
# easy copy all necessary files of specfem3d_globe into
# target directory($runbase/specfem3d_globe).
# The second option is that you can also put all specfem stuff
# in your "$runbase/specfem3d_globe"
from __future__ import print_function, division, absolute_import
import os
import argparse
from seisforward.validate_config import validate_config
from seisforward.io import load_config
from seisforward.easy_copy_specfem import easy_copy_specfem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()
    config = load_config(args.config_file)
    validate_config(config)

    specfemdir = config["data_info"]["specfemdir"]
    targetdir = os.path.join(config["data_info"]["runbase"],
                             "specfem3d_globe")

    easy_copy_specfem(specfemdir, targetdir)


if __name__ == "__main__":
    main()
