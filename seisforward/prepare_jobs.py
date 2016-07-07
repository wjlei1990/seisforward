#!/usr/bin/env python
# #####################################################################
# Scripts that prepare files for the job submission
# 1) setup_simul_run: mkdir "$runbase/specfem3d_globe/run_00XX" directories
#       for the simulatenous run and DATABASES_MPI.
# 2) perturb_cmt: perturb cmt based on values in config.yml.
# 3) setup_outputbase: mkdir './outputbase' and prepare "DATA/" and
#       "OUTPUT_FILES" for each event. Then at the running stage,
#       these two directories will be symlinked to "run_00XX"
# 4) setup_job_scripts: modify job scripts so they are ready for job
#       submission
# #####################################################################
from __future__ import print_function, division
import glob
import os
import yaml
import shutil

from .utils import safe_makedir, copyfile
from .utils import read_txt_into_list, dump_list_to_txt
from .utils import load_config
from .modify_pbs_script import modify_pbs_script
from .check_specfem import check_specfem


def perturb_cmt(eventlist, cmtdir, config):
    from perturb_cmt import gen_cmt_wrapper
    print("-" * 10 + "  perturb cmtsolutions  " + "-" * 10)
    dmoment_tensor = config["dmoment_tensor"]
    ddepth = config["ddepth"]
    dlatitude = config["dlatitude"]
    dlongitude = config["dlongitude"]

    for idx, event in enumerate(eventlist):
        cmtfile = os.path.join(cmtdir, event)
        print("%03d Peturb CMT file: %s" % (idx, cmtfile))
        if not os.path.exists(cmtfile):
            raise ValueError("cmtfile not exists: %s" % cmtfile)
        gen_cmt_wrapper(cmtfile, dmoment_tensor=dmoment_tensor,
                        dlongitude=dlongitude, dlatitude=dlatitude,
                        ddepth=ddepth, output_dir=cmtdir)


def setup_simul_run_dir(runbase, nruns):
    # copy specfem related files to sub directory
    specfemdir = os.path.join(runbase, "specfem3d_globe")

    # clean previous run_**** first
    dirlist = glob.glob(os.path.join(specfemdir, "run*"))
    print("remove dirlist: ", dirlist)
    for _dir in dirlist:
        if os.path.isdir(_dir):
            if os.path.islink(_dir):
                os.unlink(_dir)
            else:
                shutil.rmtree(_dir)
        else:
            if os.path.islink(_dir):
                os.unlink(_dir)
            else:
                shutil.remove(_dir)


def setup_outputbase(config, eventlist):
    """
    Make directory at "./outputbase" for each event:
        1) Create DATA, DATABASES_MPI, OUTPUT_FILES directories
        2) copy necessary files, including CMTSOLUTION, STATIONS,
           values_from_mesher.h and addressing.txt
    """
    outputbase = "outputbase"
    print("-"*8 + "  setup output base at: %s  " % outputbase + "-" * 8)
    simul_type = config["simulation_type"]
    filelist = ["values_from_mesher.h", "addressing.txt"]

    if simul_type == "source_invesrion":
        derivs = config["srcinv_info"]["deriv_cmt_list"]
    else:
        derivs = []

    specfemdir = os.path.join(config["data_info"]["runbase"],
                              "specfem3d_globe")

    for idx, event in enumerate(eventlist):
        _dir = os.path.join(outputbase, "%s" % event)
        print("%03d --- event %s --- dir: %s" % (idx+1, event, _dir))
        if os.path.exists(_dir):
            shutil.rmtree(_dir)
        safe_makedir(_dir)
        safe_makedir(os.path.join(_dir, "DATA"))
        safe_makedir(os.path.join(_dir, "OUTPUT_FILES"))
        safe_makedir(os.path.join(_dir, "DATABASES_MPI"))

        cmtfile1 = os.path.join("cmtfile", "%s" % event)
        cmtfile2 = os.path.join(_dir, "DATA", "CMTSOLUTION")

        copyfile(cmtfile1, cmtfile2, verbose=False)
        stafile1 = os.path.join("station", "STATIONS.%s" % event)
        stafile2 = os.path.join(_dir, "DATA", "STATIONS")
        copyfile(stafile1, stafile2, verbose=False)
        for _file in filelist:
            file1 = os.path.join(specfemdir, "OUTPUT_FILES", _file)
            file2 = os.path.join(_dir, "OUTPUT_FILES", _file)
            copyfile(file1, file2, verbose=False)

        for deriv in derivs:
            _dir = os.path.join(outputbase, "%s%s" % (event, deriv))
            safe_makedir(_dir)
            safe_makedir(os.path.join(_dir, "DATA"))
            safe_makedir(os.path.join(_dir, "OUTPUT_FILES"))
            safe_makedir(os.path.join(_dir, "DATABASES_MPI"))
            # copy stations, cmtfile into outputbase
            cmtfile1 = os.path.join("cmtfile", "%s%s" % (event, deriv))
            cmtfile2 = os.path.join(_dir, "DATA", "CMTSOLUTION")
            copyfile(cmtfile1, cmtfile2, verbose=False)

            stafile1 = os.path.join("station", "STATIONS.%s" % event)
            stafile2 = os.path.join(_dir, "DATA", "STATIONS")
            copyfile(stafile1, stafile2, verbose=False)

            # for DATA, OUTPUT_FILES and SEM, we only create symbolic link
            for _file in filelist:
                file1 = os.path.join(specfemdir, "OUTPUT_FILES", _file)
                file2 = os.path.join(_dir, "OUTPUT_FILES", _file)
                copyfile(file1, file2, verbose=False)


def split_eventlist(eventlist, nsimuls, nserials):
    nevents_total = len(eventlist)
    if nevents_total > nsimuls * nserials or \
            nevents_total < nsimuls * (nserials - 1):
        raise ValueError("Length of eventlist(%d) is in range of "
                         "nsimul_runs(%d) and nsimul_serial(%d)"
                         % (nevents_total, nsimuls, nserials))

    for i in range(nserials):
        idx_start = nsimuls * i
        idx_end = min(nsimuls * (i+1), nevents_total)
        sub_events = eventlist[idx_start:idx_end]
        job_id = i + 1
        fn = "XEVENTID.%d" % job_id
        dump_list_to_txt(fn, sub_events)

    print("Number of events total: %d" % nevents_total)
    print("Number of serial simul runs: %d" % nserials)
    print("Number of events in an simul run: %d" % nsimuls)


def prepare_jobs(config_file, eventlist_file):

    config = load_config(config_file)
    eventlist = read_txt_into_list(eventlist_file)

    specfemdir = config["data_info"]["specfemdir"]
    check_specfem(specfemdir)

    # copy specfem stuff
    print("-" * 10 + "  setup simul run sub-dir  " + "-" * 10)
    setup_simul_run_dir(config["data_info"]["runbase"],
                        config["job_info"]["nevents_per_simul_run"])

    # split the whole eventlist into sub eventlist according to
    # config[1]["nevents_per_simul_runs"]
    split_eventlist(eventlist, config["job_info"]["nevents_per_simul_run"],
                    config["job_info"]["nsimul_serial"])

    # perturb cmt files if simulation_type == source_inversion
    cmtdir = "cmtfile"
    if config["simulation_type"] == "source_inversion":
        perturb_cmt(eventlist, cmtdir, config["srcinv_info"])

    # setup output base
    setup_outputbase(config, eventlist)

    # setup job scripts
    modify_pbs_script(config, eventlist)

    print("*"*30)
    print("Please check related files and then submit jobs")
    print("Use: ./X02_submit.bash")
    print("*"*30)
