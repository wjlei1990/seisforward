#!/usr/bin/env python
 #######################################################
# Script that generate the job submission scripts on titan
# using the original job_template. For example, you have 50
# events in the XEVENTID file. But you may not want to submie
# such a big job at one time. So you want to run maybe 3
# events one time. This scripts help you to split you big
# job into smaller ones.
# #######################################################
from __future__ import print_function, division
import os
import re


def extract_number_of_nodes(specfem_parfile):
    """ extract number of nodes """
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


def modify_parfile_for_simul_run(specfemdir, nruns):
    parfile = os.path.join(specfemdir, "DATA", "Par_file")
    with open(parfile) as fh:
        content = fh.readlines()

    fo = open(parfile, "w")
    for line in content:
        line = re.sub("^NUMBER_OF_SIMULTANEOUS_RUNS.*",
                      "NUMBER_OF_SIMULTANEOUS_RUNS     = %d" % nruns,
                      line)
        line = re.sub("^BROADCAST_SAME_MESH_AND_MODEL.*",
                      "BROADCAST_SAME_MESH_AND_MODEL   = .true.",
                      line)
        fo.write(line)


def form_deriv_string_for_srcinv(deriv_cmt_list):
    full_ext_list = ["Mrr", "Mtt", "Mpp", "Mrt", "Mrp", "Mtp",
                     "dep", "lon", "lat"]

    ext_list = "ext=( \"\" "
    for _ext in deriv_cmt_list:
        if _ext not in full_ext_list:
            raise ValueError("ext incorrect: %s" % _ext)
        ext_list += "\"_%s\" " % _ext
    ext_list += ")"

    return ext_list


def modify_job_sbatch_file(inputfile, outputfile, nsimul_serial,
                           nnodes, walltime, deriv_cmt_list,
                           specfemdir, simul_type, email):
    fi = open(inputfile, "r")
    fo = open(outputfile, "w")

    content = fi.readlines()

    for line in content:
        line = re.sub(r"^#PBS -M.*", "#PBS _M %s" % email, line)
        line = re.sub(r"^#PBS -l nodes=.*", "#PBS -l nodes=%d" %
                      nnodes, line)
        line = re.sub(r"^#PBS -l walltime=.*", "#PBS -l walltime=%s" %
                      walltime, line)
        line = re.sub(r"total_serial_runs=.*",
                      "total_serial_runs=%d" % nsimul_serial,
                      line)
        line = re.sub(r"specfemdir=.*", "specfemdir=\"%s\"" % specfemdir, line)
        line = re.sub(r"^numproc=.*", "numproc=%d" % nnodes, line)

        if simul_type == "source_inversion":
            line = re.sub(r"^ext=.*", ext_list, line)

        fo.write(line)


def modify_pbs_script(config, eventlist):

    simul_type = config["simulation_type"]

    runbase = config["data_info"]["runbase"]

    nsimul_serial = config["job_info"]["nsimul_serial"]
    nevents_per_simul_run = config["job_info"]["nevents_per_simul_run"]
    walltime_per_simulation = config["job_info"]["walltime_per_simulation"]

    # calculate nodes used
    specfemdir = os.path.join(runbase, "specfem3d_globe")
    specfem_parfile = os.path.join(specfemdir, "DATA", "Par_file")
    nnodes_per_simulation = extract_number_of_nodes(specfem_parfile)
    nnodes_per_job = nnodes_per_simulation * nevents_per_simul_run

    if simul_type == "source_inversion":
        deriv_cmt_list = config["srcinv_info"]["deriv_cmt_list"]
    else:
        deriv_cmt_list = []
    # calcuate walltime
    hour, minute = \
        divmod(walltime_per_simulation * (len(deriv_cmt_list) + 1) *
               nsimul_serial, 60)
    walltime = "%d:%02d:00" % (hour, minute)

    # create job pbs script
    job_template = "job_solver.%s.bash" % simul_type
    outputfn = "job_solver.bash"
    specfemdir = os.path.join(runbase, "specfem3d_globe")

    try:
        email = config["user_info"]["email"]
    except:
        email = "xxx@princeton.edu"

    print("====== Create job scripts =======")
    print("Simulation type: %s" % simul_type)
    print("Number of events in simul run: %d" % nevents_per_simul_run)
    print("Number of serial runs: %d" % nsimul_serial)
    print("Number of deriv cmt runs: %d" % len(deriv_cmt_list))
    print("Number of nodes per simulation and job: %d * %d = %d" %
          (nnodes_per_simulation, nevents_per_simul_run, nnodes_per_job))
    print("Walltime per simul run and job: 00:%02d:00 * %d =  %s" %
          (walltime_per_simulation, nsimul_serial, walltime))
    print("-----")
    print("PBS script template: %s" % job_template)
    print("Final job script: %s" % outputfn)

    modify_job_sbatch_file(job_template, outputfn, nsimul_serial,
                           nnodes_per_job, walltime, deriv_cmt_list,
                           specfemdir, simul_type, email)

    # modify parfile to simulataneous run
    modify_parfile_for_simul_run(specfemdir, nevents_per_simul_run)
