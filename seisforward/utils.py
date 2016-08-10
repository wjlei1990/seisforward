#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import os
import yaml
import shutil


def validate_config_srcinv(config):
    if "srcinv_info" not in config:
        raise ValueError("srcinv_info must be provided if "
                         "simulation_type is source_inversion")
    keys = ["generate_deriv_cmt", "deriv_cmt_list", "dmoment_tensor",
            "ddepth", "dlatitude", "dlongitude"]
    for key in keys:
        if key not in config["srcinv_info"]:
            raise ValueError("Key(%s) missing in config srcinv_info"
                             % (key))


def validate_config_adjoint(config):
    keys = ["linkbase"]
    for key in keys:
        if key not in config["data_info"]:
            raise ValueError("Key(%s) missing in config['data_info']")


def validate_config(config):
    """ Validtate config information """
    _options = ["source_inversion", "forward_simulation",
                "adjoint_simulation"]
    simul_type = config["simulation_type"]
    if simul_type not in _options:
        raise ValueError("simulation_type(%s) not in: %s"
                         % (simul_type, _options))

    job_info = config["job_info"]
    if job_info["n_serial"] < 1:
        raise ValueError("n_serial can not be less than 1")
    if job_info["nevents_per_simul_run"] < 1:
        raise ValueError("nevents_per_simul_run should be larger "
                         "than 1")
    if job_info["walltime_per_simulation"] <= 0:
        raise ValueError("walltime_per_simulation shoulb be > 0")

    data_info = config["data_info"]
    keys = ["stationfolder", "runbase", "total_eventfile",
            "job_tag", "specfemdir"]
    if simul_type in ["source_inversion", "forward_simulation"]:
        keys.append("cmtfolder")
    elif simul_type == "adjoint_simulation":
        keys.append("adjointfolder")
    for key in keys:
        if key not in data_info:
            raise ValueError("Key(%s) not in config data_info" % (key))

    user_info = config["user_info"]
    keys = ["email"]
    for key in keys:
        if key not in user_info:
            raise ValueError("Key(%s) not in config user_info" % key)

    # validate certain simulation types
    if simul_type == "source_inversion":
        validate_config_srcinv(config)
    elif simul_type == "adjoint_simulation":
        validate_config_adjoint(config)


def load_config(filename):
    with open(filename) as fh:
        config = yaml.load(fh)
    # validate_config(config)
    return config


def dump_yaml(content, filename):
    with open(filename, 'w') as fh:
        yaml.dump(content, fh, indent=2)


def safe_makedir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def check_exist(filename):
    if not os.path.exists(filename):
        raise ValueError("Path not exists: %s" % filename)


def read_txt_into_list(filename):
    with open(filename, "r") as f:
        return [x.rstrip("\n") for x in f]


def dump_list_to_txt(filename, content):
    with open(filename, 'w') as f:
        for line in content:
            f.write("%s\n" % line)


def cleantree(folder):
    if not os.path.exists(folder):
        return
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception, e:
            print(e)


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(src):
        raise ValueError("Src dir not exists: %s" % src)
    if not os.path.exists(dst):
        raise ValueError("Dest dir not exists: %s" % dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def copyfile(origin_file, target_file, verbose=True):
    if not os.path.exists(origin_file):
        raise ValueError("No such file: %s" % origin_file)

    if not os.path.exists(os.path.dirname(target_file)):
        os.makedirs(os.path.dirname(target_file))

    if verbose:
        print("Copy file:[%s --> %s]" % (origin_file, target_file))
    shutil.copy2(origin_file, target_file)


def get_permission():
    answer = raw_input("[Y/n]:")
    if answer == "Y":
        return True
    elif answer == "n":
        return False
    else:
        raise ValueError("answer incorrect: %s" % answer)
