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


def modify_specfem_parfile(config, specfemdir):

    nevents_per_simul_run = config["job_config"]["nevents_per_simul_run"]
    simul_type = config["simulation"]["type"]

    if simul_type == "forward_simulation":
        save_forward = config["simulation"]["save_forward"]
    else:
        save_forward = False

    record_length = config["simulation"]["record_length_in_minutes"]

    # modify parfile to simulataneous run
    modify_parfile_for_simul_run(
        specfemdir, nevents_per_simul_run, simul_type, save_forward,
        record_length)


def get_simul_param(simul_type):
    """
    Get simulation type number and save_froward from simulation
    type
    """
    if simul_type == "line_search":
        simul_num = 1
    elif simul_type == "forward_simulation":
        simul_num = 1
    elif simul_type == "adjoint_simulation":
        simul_num = 3
    else:
        raise NotImplementedError("Unrecognized simulation type: %s"
                                  % simul_type)

    return simul_num


def modify_parfile_for_simul_run(
        specfemdir, nruns, simul_type, save_forward,
        record_len_in_mins):
    """
    Modify the Par_file based on simulation type and number of
    simulataneous runs:
    1) SIMULATION_TYPE; 2) SAVE_FORWARD;
    3) NUMBER_OF_SIMULATANEOUS_RUNS 4) BROADCASE_SAME_MESH_AND_MODEL
    """
    parfile = os.path.join(specfemdir, "DATA", "Par_file")
    with open(parfile) as fh:
        content = fh.readlines()

    simul_num = get_simul_param(simul_type)
    if save_forward:
        save_flag = '.true.'
    else:
        save_flag = '.false.'
    print("Simulation type, number and save forward: %s, %d, %s"
          % (simul_type, simul_num, save_forward))

    fo = open(parfile, "w")
    for line in content:
        line = re.sub("^SIMULATION_TYPE.*",
                      "SIMULATION_TYPE                 = %d" % simul_num,
                      line)
        line = re.sub("^SAVE_FORWARD.*",
                      "SAVE_FORWARD                    = %s " % save_flag,
                      line)
        line = re.sub("^NUMBER_OF_SIMULTANEOUS_RUNS.*",
                      "NUMBER_OF_SIMULTANEOUS_RUNS     = %d" % nruns,
                      line)
        line = re.sub("^BROADCAST_SAME_MESH_AND_MODEL.*",
                      "BROADCAST_SAME_MESH_AND_MODEL   = .true.",
                      line)
        line = re.sub("^RECORD_LENGTH_IN_MINUTES.*",
                      "RECORD_LENGTH_IN_MINUTES        = {:.1f}".format(
                          record_len_in_mins),
                      line)
        fo.write(line)
