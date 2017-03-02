#!/usr/bin/env python
"""
This file contains class and methods for setup line search forward
simulations.
"""
from __future__ import print_function, division, absolute_import
import os
import re

from .generate_pbs_script import generate_pbs_script, modify_specfem_parfile, \
    get_walltime, get_nnodes
from .check_specfem import check_specfem
from .easy_copy_specfem import easy_copy_specfem
from .forward_manager import setup_entry_dir, dump_eventlist, ForwardManager
from .io import dump_yaml, read_txt_into_list, dump_list_to_txt
from .utils import clean_specfem, get_package_path, make_title, \
    check_folders_exist, safe_makedir


def create_job_folder(job_dir, entries, config, specfem_base, model_perturb):
    """
    create job folder, to hold XEVENTID.* and pbs script.
    Keep an copy of specfem stuff(excluding the model file because of
    its size) at local dir. So jobs could be submitted inside the job
    dir indepandently.
    """
    print("*"*20 + "\nCreat job sub folders: %s" % job_dir)
    if not os.path.exists(job_dir):
        os.makedirs(job_dir)

    n_serial = config["job_config"]["n_serial"]
    n_simul = config["job_config"]["nevents_per_simul_run"]
    dump_eventlist(entries, job_dir, n_serial, n_simul)

    # copy config.yaml file
    config_yaml_fn = os.path.join(job_dir, "config.yml")
    dump_yaml(config, config_yaml_fn)

    # make a specfem dir locally for the job so it could be
    # run locally
    local_specfem = os.path.join(job_dir, "specfem3d_globe")
    safe_makedir(local_specfem)
    easy_copy_specfem(specfem_base, local_specfem, model_flag=False)
    clean_specfem(local_specfem)

    # copy scripts template
    simul_type = config["simulation_type"]
    template = os.path.join(
        get_package_path(), "template", "job_template",
        "job_solver.%s_subs.bash" % simul_type)
    outputfn = os.path.join(job_dir, "job_solver.bash")
    generate_pbs_script(template, outputfn, config, local_specfem,
                        model_perturb=model_perturb)

    modify_specfem_parfile(config, local_specfem)


def modify_ls_overall_job_script(template, outputfn, config):
    """
    modify the line search onverall job script
    """
    # for the model perturbs
    model_perturbs = config["model_perturbations"]
    mp_string = "model_perturbs=("
    for mp in model_perturbs:
        mp_string += '"%.4f" ' % mp
    mp_string += ")"

    # get nnodes and walltime
    walltime, _ = get_walltime(config)

    specfemdir = os.path.join(config["runbase"], "specfem3d_globe")
    nnodes_per_job = get_nnodes(config, specfemdir)
    email = config["user_info"]["email"]

    content = read_txt_into_list(template)
    new_content = []
    for line in content:
        line = re.sub(r"^#PBS -M.*", "#PBS _M %s" % email, line)
        line = re.sub(r"^#PBS -l nodes=.*", "#PBS -l nodes=%d" %
                      (nnodes_per_job+5), line)
        line = re.sub(r"^#PBS -l walltime=.*", "#PBS -l walltime=%s" %
                      walltime, line)
        line = re.sub(r"^model_perturbs=.*", mp_string, line)
        new_content.append(line)

    dump_list_to_txt(new_content, outputfn)


def copy_overall_job_script(config, job_dirs):
    simul_type = config["simulation_type"]
    template = os.path.join(
        get_package_path(), "template", "job_template",
        "job_solver.%s.bash" % simul_type)

    for dirname in job_dirs:
        # copy to one upper level
        upper_dir = os.path.dirname(dirname)
        outputfn = os.path.join(upper_dir, "job_solver_all.bash")
        modify_ls_overall_job_script(template, outputfn, config)


class LineSearchSolver(ForwardManager):
    """
    Forward job creator
    """
    def get_new_entries(self, tag):
        print(make_title("Retrieve jobs from DB"))
        n_serial = self.config["job_config"]["n_serial"]
        n_simul = self.config["job_config"]["nevents_per_simul_run"]
        num_to_fetch = n_serial * n_simul
        print("n_serial * n_simul = n_total: %d * %d = %d"
              % (n_serial, n_simul, num_to_fetch))

        runbase = self.config["runbase"]
        job_entries = self.retrieve_new_entries_from_db(
            tag=tag, num_to_fetch=num_to_fetch)

        job_base = os.path.join(runbase, "jobs")
        njobs = len(job_entries)
        print("Number of jobs: %d" % njobs)

        job_prefix = self.config["job_folder_prefix"]
        job_dirs = [
            os.path.join(
                job_base, "job_%s_%02d" % (job_prefix, idx+1), tag)
            for idx in range(njobs)]

        check_folders_exist(job_dirs)
        return job_dirs, job_entries

    def create_jobs(self):
        config = self.config

        runbase = config["runbase"]
        specfem_base = os.path.join(runbase, "specfem3d_globe")
        check_specfem(specfem_base, model_flag=False)

        model_perturbs = config["model_perturbations"]
        for mp in model_perturbs:
            # for each perturbation values, create sub job dir
            tag = "perturb_%.4f" % mp
            print(make_title("Model Perturbation: %.4f(%s)" % (mp, tag)))
            job_dirs, job_entries = self.get_new_entries(tag)

            njobs = len(job_entries)
            idx = 0
            for _dir, _entries in zip(job_dirs, job_entries):
                idx += 1
                print(make_title("Create job[%d/%d]" % (idx, njobs)))
                print("job dir: %s" % _dir)
                print("Number of entries: %d" % len(_entries))
                setup_entry_dir(_entries, specfem_base)
                create_job_folder(_dir, _entries, config, specfem_base,
                                  mp)

        # use the last mp job_dirs to copy the overall job script
        copy_overall_job_script(config, job_dirs)
