#!/usr/bin/env python
# ##########################
# easy copy all necessary files of specfem3d_globe into
# target directory($runbase/specfem3d_globe).
# The second option is that you can also put all specfem stuff
# in your "$runbase/specfem3d_globe"
from __future__ import print_function, division, absolute_import
import os
import argparse
import glob
import shutil
from .utils import copyfile, load_config
from .check_specfem import check_specfem


def safe_copy(fn, specfemdir, targetdir):
    origin_file = os.path.join(specfemdir, fn)
    target_file = os.path.join(targetdir, fn)

    copyfile(origin_file, target_file)


def safe_copy_model_file(specfemdir, targetdir):
    origindir = os.path.join(specfemdir, "DATABASES_MPI")
    model_files = glob.glob(os.path.join(origindir, "*"))

    if len(model_files) == 0:
        raise ValueError("No model files at dir: %s" % origindir)

    target_model_dir = os.path.join(targetdir, "DATABASES_MPI")
    if not os.path.exists(target_model_dir):
        os.makedirs(target_model_dir)

    print("-"*10 + "\nCopy model files:")
    for _file in model_files:
        print("[%s --> %s]" % (_file, target_model_dir))
        shutil.copy2(_file, target_model_dir)


def easy_copy_specfem(specfemdir, targetdir):

    if not os.path.exists(specfemdir):
        raise ValueError("No specfem dir: %s" % specfemdir)

    check_specfem(specfemdir)

    print("--------------------------")
    filelist = ["bin/xspecfem3D", "OUTPUT_FILES/addressing.txt",
                "OUTPUT_FILES/values_from_mesher.h",
                "DATA/Par_file"]
    for fn in filelist:
        safe_copy(fn, specfemdir, targetdir)
    safe_copy_model_file(specfemdir, targetdir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()
    config = load_config(args.config_file)

    print("******************************************")
    specfemdir = config["data_info"]["specfemdir"]
    print("The directory of specfem package: %s" % specfemdir)

    targetdir = os.path.join(config["data_info"]["runbase"],
                             "specfem3d_globe")
    print("Target dir: %s" % targetdir)

    easy_copy_specfem(specfemdir, targetdir)


if __name__ == "__main__":
    main()
