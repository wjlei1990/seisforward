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
from .utils import check_exist, get_model_perturbation_string


def extract_number_of_mpis(specfem_parfile):
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


def modify_pbs_header(line, nnodes, walltime, email):
    # only forward simulation contains PBS header
    line = re.sub(r"^#PBS -M.*", "#PBS -M %s" % email, line)
    line = re.sub(r"^#PBS -l nodes=.*", "#PBS -l nodes=%d" %
                  (nnodes+1), line)
    line = re.sub(r"^#PBS -l walltime=.*", "#PBS -l walltime=%s" %
                  walltime, line)
    return line


def modify_lsf_header(line, nnodes, walltime):
    line = re.sub(r"^#BSUB -nnodes .*",
                  "#BSUB -nnodes {}".format(nnodes),
                  line)
    line = re.sub(r"^#BSUB -W .*",
                  "#BSUB -W {}".format(walltime),
                  line)
    return line


def modify_job_batch_file(job_template, job_script,
                          n_serial, nmpis, nnodes,
                          walltime, timeout_sec,
                          specfemdir, linkbase,
                          simul_type, email, batch_system_config,
                          modelbase):
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

    batch_type = batch_system_config["name"]

    new_content = []
    for line in content:
        if simul_type == "forward_simulation":
            if batch_type == "lsf":
                line = modify_lsf_header(line, nnodes, walltime)
            elif batch_type == "pbs":
                line = modify_pbs_header(line, nnodes, walltime, email)
            else:
                raise ValueError("Unknown batch system: {}".format(batch_type))

        line = re.sub(r"^specfemdir=.*",
                      "specfemdir=\"{}\"".format(specfemdir),
                      line)
        line = re.sub(r"^linkbase=.*", "linkbase=\"%s\"" % linkbase, line)
        line = re.sub(r"^model_base=.*", "model_base=\"%s\"" % modelbase,
                      line)
        line = re.sub(r"^total_serial_runs=.*",
                      "total_serial_runs=%d" % n_serial, line)
        line = re.sub(r"^timeout_aprun=.*", "timeout_aprun=%d" % timeout_sec,
                      line)

        if batch_type == "lsf":
            nmpi_per_res = batch_system_config["nmpi_per_res"]
            ncpu_per_res = batch_system_config["ncpu_per_res"]
            if ncpu_per_res > nmpi_per_res or nmpi_per_res % ncpu_per_res:
                raise ValueError("Incorrect values combos for ncpu and nmpi "
                                 "per res: {}, {}".format(ncpu_per_res,
                                                          nmpi_per_res))
            nres = int(nmpis / nmpi_per_res)
            line = re.sub(r"^nres=.*", "nres={}".format(nres), line)
            line = re.sub(r"^nmpi_per_res=.*",
                          "nmpi_per_res={}".format(nmpi_per_res),
                          line)
            line = re.sub(r"^ncpu_per_res=.*",
                          "ncpu_per_res={}".format(ncpu_per_res),
                          line)
        elif batch_type == "pbs":
            line = re.sub(r"^nmpis=.*", "nmpis=%d" % nmpis, line)
        else:
            raise ValueError("Unknow batch system: {}".format(batch_type))

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
    simul_type = config["simulation"]["type"]

    if simul_type == "forward_simulation":
        total_time_in_min = \
            walltime_per_simulation * n_serial
        print("Walltime per simul run, n_serial: %d min * %d" %
              (walltime_per_simulation, n_serial))
    elif simul_type == "line_search":
        n_perturbs = len(config["model_perturbations"])
        total_time_in_min = \
            walltime_per_simulation * n_serial * n_perturbs + \
            n_serial * n_perturbs * 1.0
        print("Walltime per simul run, n_serial, n_perturbs: "
              "%d min * %d * %d" %
              (walltime_per_simulation, n_serial, n_perturbs))
    else:
        raise ValueError("Error simulation type: %s" % simul_type)

    hour, minute = divmod(total_time_in_min, 60)
    batch_type = config["batch_system"]["name"]
    if batch_type == "lsf":
        walltime = "%d:%02d" % (hour, minute)
    elif batch_type == "pbs":
        walltime = "%d:%02d:00" % (hour, minute)

    print("Total Walltime[{}]: {}".format(batch_type, walltime))

    # give extra time to timeout command incase some jobs may take longer
    timeout_sec = walltime_per_simulation * 60 * 1.5

    return walltime, timeout_sec


def get_nnodes(config, specfemdir):
    # calculate nodes used
    nevents_per_simul_run = config["job_config"]["nevents_per_simul_run"]

    specfem_parfile = os.path.join(specfemdir, "DATA", "Par_file")
    nmpis_per_simulation = extract_number_of_mpis(specfem_parfile)
    nmpis_per_job = nmpis_per_simulation * nevents_per_simul_run
    print("Number of mpis per simulation and job: %d * %d = %d" %
          (nmpis_per_simulation, nevents_per_simul_run, nmpis_per_job))

    batch_config = config["batch_system"]
    nmpis_per_node = \
        batch_config["ngpu_per_node"] * batch_config["nmpi_per_res"]
    nnodes_per_job = int(nmpis_per_job / nmpis_per_node)
    print("Number of total mpis and nodes: {} / ({} * {}) = "
          "{}".format(nmpis_per_job, batch_config["ngpu_per_node"],
                      batch_config["nmpi_per_res"], nnodes_per_job))

    return nmpis_per_job, nnodes_per_job


def generate_lsf_script(template, outputfn, config, job_specfemdir):
    simul_type = config["simulation"]["type"]
    runbase_info = config["runbase_info"]
    runbase = runbase_info["runbase"]

    nmpis_per_job, nnodes_per_job = get_nnodes(config, job_specfemdir)
    walltime, timeout_sec = get_walltime(config)

    print("====== Create lsf job scripts =======")
    print("Simulation type: %s" % simul_type)

    use_local_model_file = runbase_info["copy_model_to_sub_job_folder"]
    if simul_type in ["forward_simulation"]:
        linkbase = os.path.join(runbase, "archive")

        if use_local_model_file:
            # if use_local_model_file, then model files are from
            # job directory
            modelbase = os.path.join(
                job_specfemdir, "DATABASES_MPI")
        else:
            # if not, use model files from runbase specfem directory
            modelbase = os.path.join(
                runbase, "specfem3d_globe", "DATABASES_MPI")
    else:
        raise ValueError("Unkonwn simul type: {}".format(simul_type))

    check_exist(linkbase)
    check_exist(modelbase)

    email = config["user_info"]["email"]
    n_serial = config["job_config"]["n_serial"]
    modify_job_batch_file(template, outputfn,
                          n_serial, nmpis_per_job, nnodes_per_job,
                          walltime, timeout_sec,
                          job_specfemdir, linkbase,
                          simul_type, email, config["batch_system"],
                          modelbase)

    print("-----")
    print("LSF script template: %s" % template)
    print("Final job script: %s" % outputfn)


def generate_pbs_script(template, outputfn, config, specfemdir,
                        model_perturb=None):

    simul_type = config["simulation"]["type"]
    runbase_info = config["runbase_info"]
    runbase = runbase_info["runbase"]

    nmpis_per_job, nnodes_per_job = get_nnodes(config, specfemdir)
    walltime, timeout_sec = get_walltime(config)

    print("====== Create pbs job scripts =======")
    print("Simulation type: %s" % simul_type)

    use_local_model_file = runbase_info["copy_model_to_sub_job_folder"]

    if simul_type in ["forward_simulation", "adjoint_simulation"]:
        linkbase = os.path.join(runbase, "archive")

        if use_local_model_file:
            modelbase = os.path.join(
                specfemdir, "DATABASES_MPI")
        else:
            modelbase = os.path.join(
                runbase, "specfem3d_globe", "DATABASES_MPI")

    elif simul_type in ["line_search"]:
        linkbase = os.path.join(
            runbase, "archive", get_model_perturbation_string(model_perturb))
        modelbase = os.path.join(
            runbase, "specfem3d_globe",
            "DATABASES_MPI-%s" % get_model_perturbation_string(model_perturb,
                                                               False))
    else:
        raise ValueError("Unkonwn simul type: %s" % simul_type)
    check_exist(linkbase)
    check_exist(modelbase)

    email = config["user_info"]["email"]
    n_serial = config["job_config"]["n_serial"]
    modify_job_batch_file(template, outputfn,
                          n_serial, nmpis_per_job, nnodes_per_job,
                          walltime, timeout_sec,
                          specfemdir, linkbase,
                          simul_type, email, config["batch_system"],
                          modelbase)

    print("-----")
    print("PBS script template: %s" % template)
    print("Final job script: %s" % outputfn)
