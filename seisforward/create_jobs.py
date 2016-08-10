#!/usr/bin/env python
"""
Scripts that splits a large eventlist file into subfolders.
For example, you have a eventlist contains 320 events.
and you want to split it into 50 events/per file. There will
be 6 files generated. The first 5 files will have 50 events
while the last will have 20 events.
The output job scripts will be put at "$runbase/jobs"
"""
from __future__ import print_function, division, absolute_import
import os
import sys
import math
import argparse
import shutil
from .utils import copytree, cleantree, copyfile, get_permission
from .utils import read_txt_into_list, dump_list_to_txt
from .utils import load_config, dump_yaml, validate_config
from .check_specfem import check_specfem


def print_split_summary(nevents_total, nevents_per_job, njobs):
    print("*"*20 + "\nSplit eventlist")
    print("Number of events:", nevents_total)
    print("Jobs per bundle:", nevents_per_job)
    print("Number of jobs:", njobs)


def check_eventlist(eventlist):
    if len(set(eventlist)) != len(eventlist):
        raise ValueError("There are duplicate elements in eventlist")


def split_eventlist(config):
    """
    Split the total event list to sub-job eventlist
    """
    nevents_per_job = \
        config["job_info"]["n_serial"] * \
        config["job_info"]["nevents_per_simul_run"]

    # read the overall eventlist
    eventlist = read_txt_into_list(config["data_info"]["total_eventfile"])
    nevents_total = len(eventlist)

    if nevents_total % nevents_per_job != 0:
        raise ValueError("nevents_total(%d) must be multiples of "
                         "nevents_per_job(%d)"
                         % (nevents_total, nevents_per_job))

    njobs = int(math.ceil(nevents_total/float(nevents_per_job)))

    num_total = 0
    eventlist_dict = {}
    for i in range(1, njobs+1):
        start_idx = (i-1) * nevents_per_job
        end_idx = min(i * nevents_per_job, nevents_total)
        print("job: %3d -- event index: [%4d --> %4d)" %
              (i, start_idx, end_idx))
        eventlist_dict[i] = eventlist[start_idx:end_idx]
        num_total += len(eventlist_dict[i])

    if num_total != nevents_total:
        raise ValueError("Event split Error!!! %d != %d"
                         % (num_total, nevents_total))

    print_split_summary(nevents_total, nevents_per_job, njobs)
    return eventlist_dict


def check_adjoint_file(eventlist, adjointfolder):
    err = 0
    for event in eventlist:
        adjoint_fn = os.path.join(adjointfolder, "%s.adjoint.h5" % event)
        if not os.path.exists(adjoint_fn):
            err = -1
            print("Missing adjoint file: %s" % adjoint_fn)

    if err != 0:
        raise ValueError("Missing adjoint asdf file")


def check_job_folder_exist(targetdir_list):
    clean_status = 1
    for targetdir in targetdir_list:
        if os.path.exists(targetdir):
            print("job folder exists: %s" % targetdir)
            clean_status = 0

    if clean_status == 0:
        print("Removed?")
        if get_permission():
            for _dir in targetdir_list:
                if os.path.exists(_dir):
                    cleantree(_dir)
        else:
            sys.exit(0)


def copy_cmtfiles(eventlist, cmtfolder, targetcmtdir):
    print("copy cmt:[%s --> %s]" % (cmtfolder, targetcmtdir))
    for _event in eventlist:
        origincmt = os.path.join(cmtfolder, _event)
        targetcmt = os.path.join(targetcmtdir, _event)
        copyfile(origincmt, targetcmt, verbose=False)


def copy_stations(eventlist, stafolder, targetstadir, tag="forward"):
    if tag not in ["forward", "adjoint"]:
        raise ValueError("tag(%s) must be 'forward' or 'adjoint'")
    print("copy stattion(%s):[%s --> %s]" % (tag, stafolder, targetstadir))
    if tag == "forward":
        prefix = "STATIONS"
    elif tag == "adjoint":
        prefix = "STATIONS_ADJOINT"
    for _event in eventlist:
        originsta = os.path.join(stafolder, "%s.%s" % (prefix, _event))
        targetsta = os.path.join(targetstadir, "%s.%s" % (prefix, _event))
        copyfile(originsta, targetsta, verbose=False)


def get_package_path():
    import seisforward
    return seisforward.__path__[0]


def dump_eventlist_subdir(eventlist, targetdir):
        fn = os.path.join(targetdir, "_XEVENTID.all")
        dump_list_to_txt(fn, eventlist)


def copy_scripts_template(simulation_type, targetdir):
    package_path = get_package_path()

    # copy scripts to generate deriv cmt files
    if simulation_type == "source_inversion":
        folder = os.path.join(package_path, "template", "perturb_cmt")
        copytree(folder, targetdir)

    # copy scripts template
    template_folder = os.path.join(package_path, "template",
                                   "job_template")
    print("Copy scripts template:[%s --> %s]" %
          (template_folder, targetdir))

    filelist = ["X01_prepare_dir.py", "X02_submit.bash",
                "X03_archive_data.pbs"]

    if simulation_type == "adjoint_simulation":
        filelist.append("X00_copy_adjoint.py")

    for _file in filelist:
        path = os.path.join(template_folder, _file)
        shutil.copy(path, targetdir)

    pbs_script = os.path.join(template_folder, "job_solver.%s.bash"
                              % simulation_type)
    shutil.copy(pbs_script, targetdir)


def create_job_folder(eventlist_dict, config):
    # create job folder
    tag = config["data_info"]["job_tag"]
    stafolder = config["data_info"]["stationfolder"]
    simulation_type = config["simulation_type"]
    adjointfolder = config["data_info"]["adjointfolder"]

    print("*"*20 + "\nCreat job sub folders")
    jobs_dir = os.path.join(config["data_info"]["runbase"], "jobs")
    targetdirs = [os.path.join(jobs_dir, "job_%s_%02d" % (tag, idx))
                  for idx in eventlist_dict]
    check_job_folder_exist(targetdirs)

    for _idx, targetdir in enumerate(targetdirs):
        if not os.path.exists(targetdir):
            os.makedirs(targetdir)

        job_idx = _idx + 1
        print("="*5 + "\nJob id: %d" % job_idx)
        eventlist = eventlist_dict[job_idx]
        dump_eventlist_subdir(eventlist, targetdir)

        # copy original cmt file and station file
        if simulation_type == "forward_simulation":
            cmtfolder = config["data_info"]["cmtfolder"]
            targetcmtdir = os.path.join(targetdir, "cmtfile")
            copy_cmtfiles(eventlist, cmtfolder, targetcmtdir)
            targetstadir = os.path.join(targetdir, "station")
            copy_stations(eventlist, stafolder, targetstadir,
                          tag="forward")
        else:
            targetstadir = os.path.join(targetdir, "station")
            copy_stations(eventlist, stafolder, targetstadir,
                          tag="adjoint")
            check_adjoint_file(eventlist, adjointfolder)

        # copy scripts template
        copy_scripts_template(simulation_type, targetdir)

        # copy config.yaml file
        config_yaml_fn = os.path.join(targetdir, "config.yml")
        dump_yaml(config, config_yaml_fn)

    return targetdirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()
    config = load_config(args.config_file)
    validate_config(config)

    eventlist_dict = split_eventlist(config)

    specfemdir = os.path.join(config["data_info"]["runbase"],
                              "specfem3d_globe")
    check_specfem(specfemdir)

    # create job folder
    create_job_folder(eventlist_dict, config)


if __name__ == "__main__":
    main()
