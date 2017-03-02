#!/usr/bin/env python
# #######################################################
# Script that generate the job submission scripts on titan
# using the original job_template. For example, you have 50
# events in the XEVENTID file. But you may not want to submie
# such a big job at one time. So you want to run maybe 3
# events one time. This scripts help you to split you big
# job into smaller ones.
# 1) modify the pbs job script
# 2) moidfy the Par_file: to match the current run
# 3) check specfem
# #######################################################
from __future__ import print_function, division, absolute_import
import os
import re
from .utils import check_exist


def extract_number_of_nodes(specfem_parfile):
    """
    Extract number of nodes from specfem parfile
    nproc = NPROC_XI * NPROC_ETA * NCHUNKS
    """
    with open(specfem_parfile) as fh:
        content = fh.readlines()
    for line in content:
        if re.search(r'^NPROC_XI', line):
            nproc_xi = int(line.split()[-1])
        if re.search(r'^NPROC_ETA', line):
            nproc_eta = int(line.split()[-1])
        if re.search(r'^NCHUNKS', line):
            nchunks = int(line.split()[-1])
    nproc = nproc_xi * nproc_eta * nchunks
    return nproc


def get_simul_param(simul_type):
    """
    Get simulation_type number and save_froward from simulation
    type
    """
    if simul_type == "line_search":
        simul_num = 1
        save_forward = ".false."
    elif simul_type == "forward_simulation":
        simul_num = 1
        save_forward = ".true."
    elif simul_type == "adjoint_simulation":
        simul_num = 3
        save_forward = ".false."
    else:
        raise NotImplementedError("Unrecognized simulation type: %s"
                                  % simul_type)

    return simul_num, save_forward


def modify_parfile_for_simul_run(specfemdir, nruns, simul_type):
    """
    Modify the Par_file based on simulation type and number of
    simulataneous runs:
    1) SIMULATION_TYPE; 2) SAVE_FORWARD;
    3) NUMBER_OF_SIMULATANEOUS_RUNS 4) BROADCASE_SAME_MESH_AND_MODEL
    """
    parfile = os.path.join(specfemdir, "DATA", "Par_file")
    with open(parfile) as fh:
        content = fh.readlines()

    simul_num, save_forward = get_simul_param(simul_type)
    print("Simulation type, number and save forward: %s, %d, %s"
          % (simul_type, simul_num, save_forward))

    fo = open(parfile, "w")
    for line in content:
        line = re.sub("^SIMULATION_TYPE.*",
                      "SIMULATION_TYPE                 = %d" % simul_num,
                      line)
        line = re.sub("^SAVE_FORWARD.*",
                      "SAVE_FORWARD                    = %s " % save_forward,
                      line)
        line = re.sub("^NUMBER_OF_SIMULTANEOUS_RUNS.*",
                      "NUMBER_OF_SIMULTANEOUS_RUNS     = %d" % nruns,
                      line)
        line = re.sub("^BROADCAST_SAME_MESH_AND_MODEL.*",
                      "BROADCAST_SAME_MESH_AND_MODEL   = .true.",
                      line)
        fo.write(line)


def form_deriv_string_for_srcinv(deriv_cmt_list):
    """
    for source inversion(obsolete)
    """
    full_ext_list = ["Mrr", "Mtt", "Mpp", "Mrt", "Mrp", "Mtp",
                     "dep", "lon", "lat"]

    ext_list = "ext=( \"\" "
    for _ext in deriv_cmt_list:
        if _ext not in full_ext_list:
            raise ValueError("ext incorrect: %s" % _ext)
        ext_list += "\"_%s\" " % _ext
    ext_list += ")"

    return ext_list


def modify_job_sbatch_file(job_template, job_script, n_serial, nnodes,
                           walltime, timeout_sec,
                           specfemdir, linkbase, modelbase, simul_type,
                           email):
    """
    Modify the pbs job script, based on the job template
    1) email: user email
    2) number of nodes: pbs header(nnodes)
    3) walltime: total walltime in pbs header
    4) walltime_per_simulation: for timeout aprun
    5) total_serial_runs: number of serial apruns(nserial)
    6) specfemdir: the directory of specfem to run the code
    7) linkbase: rundir
    8) modebase: model directory
    4) numproc: in aprun, using GPU, so same as nnodes
    5) linkbase: the linkbase(to be linked as run****)
    """
    with open(job_template) as fh:
        content = [line.rstrip() for line in fh]

    new_content = []
    for line in content:
        if simul_type == "forward_simulation":
            # only forward simulation contains PBS header
            line = re.sub(r"^#PBS -M.*", "#PBS _M %s" % email, line)
            line = re.sub(r"^#PBS -l nodes=.*", "#PBS -l nodes=%d" %
                          (nnodes+5), line)
            line = re.sub(r"^#PBS -l walltime=.*", "#PBS -l walltime=%s" %
                          walltime, line)

        line = re.sub(r"^specfemdir=.*", "specfemdir=\"%s\"" % specfemdir,
                      line)
        line = re.sub(r"^linkbase=.*", "linkbase=\"%s\"" % linkbase, line)
        line = re.sub(r"^model_base=.*", "model_base=\"%s\"" % modelbase,
                      line)
        line = re.sub(r"^total_serial_runs=.*",
                      "total_serial_runs=%d" % n_serial, line)
        line = re.sub(r"^numproc=.*", "numproc=%d" % nnodes, line)
        line = re.sub(r"^timeout_aprun=.*", "timeout_aprun=%d" % timeout_sec,
                      line)

        new_content.append(line)

    with open(job_script, 'w') as fh:
        for line in new_content:
            fh.write("%s\n" % line)


def get_walltime(config):
    # calcuate walltime
    n_serial = config["job_config"]["n_serial"]
    print("Number of serial runs: %d" % n_serial)
    walltime_per_simulation = config["job_config"]["walltime_per_simulation"]
    # give every aprun one more minute(for gpu failure recovery)
    simul_type = config["simulation_type"]

    if simul_type == "forward_simulation":
        total_time_in_min = \
            walltime_per_simulation * n_serial + n_serial * 1.0
        print("Walltime per simul run, n_serial: 00:%02d:00 * %d" %
              (walltime_per_simulation, n_serial))
    elif simul_type == "line_search":
        n_perturbs = len(config["model_perturbations"])
        total_time_in_min = \
            walltime_per_simulation * n_serial * n_perturbs + \
            n_serial * n_perturbs * 1.0
        print("Walltime per simul run, n_serial, n_perturbs: "
              "00:%02d:00 * %d * %d" %
              (walltime_per_simulation, n_serial, n_perturbs))
    else:
        raise ValueError("Error simulation type: %s" % simul_type)

    hour, minute = divmod(total_time_in_min, 60)
    walltime = "%d:%02d:00" % (hour, minute)

    print("Total Walltime: %s" % walltime)
    # give extra time to timeout command incase some jobs may take longer
    timeout_sec = walltime_per_simulation * 60 * 1.5

    return walltime, timeout_sec


def get_nnodes(config, specfemdir):
    # calculate nodes used
    nevents_per_simul_run = config["job_config"]["nevents_per_simul_run"]
    specfem_parfile = os.path.join(specfemdir, "DATA", "Par_file")
    nnodes_per_simulation = extract_number_of_nodes(specfem_parfile)
    nnodes_per_job = nnodes_per_simulation * nevents_per_simul_run
    print("Number of events in simul run: %d" % nevents_per_simul_run)
    print("Number of nodes per simulation and job: %d * %d = %d" %
          (nnodes_per_simulation, nevents_per_simul_run, nnodes_per_job))
    return nnodes_per_job


def generate_pbs_script(template, outputfn, config, specfemdir,
                        model_perturb=None):

    simul_type = config["simulation_type"]
    runbase = config["runbase"]

    nnodes_per_job = get_nnodes(config, specfemdir)
    walltime, timeout_sec = get_walltime(config)

    print("====== Create job scripts =======")
    print("Simulation type: %s" % simul_type)

    if simul_type in ["forward_simulation", "adjoint_simulation"]:
        linkbase = os.path.join(runbase, "archive")
        modelbase = os.path.join(runbase, "specfem3d_globe", "DATABASES_MPI")
    elif simul_type in ["line_search"]:
        linkbase = os.path.join(runbase, "archive", "perturb_%.4f" %
                                model_perturb)
        modelbase = os.path.join(
            runbase, "specfem3d_globe", "DATABASES_MPI-%.4f" % model_perturb)
    else:
        raise ValueError("Error: %s" % simul_type)
    check_exist(linkbase)
    check_exist(modelbase)

    try:
        email = config["user_info"]["email"]
    except:
        email = "xxx@princeton.edu"

    n_serial = config["job_config"]["n_serial"]
    modify_job_sbatch_file(template, outputfn, n_serial, nnodes_per_job,
                           walltime, timeout_sec,
                           specfemdir, linkbase, modelbase, simul_type, email)

    print("-----")
    print("PBS script template: %s" % template)
    print("Final job script: %s" % outputfn)


def modify_specfem_parfile(config, specfemdir):

    nevents_per_simul_run = config["job_config"]["nevents_per_simul_run"]
    simul_type = config["simulation_type"]

    # modify parfile to simulataneous run
    modify_parfile_for_simul_run(specfemdir, nevents_per_simul_run,
                                 simul_type)
