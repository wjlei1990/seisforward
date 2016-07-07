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
import os
from seisforward.prepare_jobs import prepare_jobs


if __name__ == "__main__":
    config_file = "config.yml"
    eventlist_file = "_XEVENTID.all"

    if not os.path.exists(config_file):
        raise ValueError("Missing config file: %s" % config_file)

    if not os.path.exists(eventlist_file):
        raise ValueError("Missing eventlist file: %s" % eventlist_file)

    prepare_jobs(config_file, eventlist_file)
