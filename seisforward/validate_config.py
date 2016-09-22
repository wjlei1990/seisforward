#!/usr/bin/env python
from __future__ import print_function, division, absolute_import


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


def validate_job_config(job_config):
    if job_config["n_serial"] < 1:
        raise ValueError("n_serial should be >= 1")
    if job_config["nevents_per_simul_run"] < 1:
        raise ValueError("nevents_per_simul_run should be larger "
                         "than 1")
    if job_config["walltime_per_simulation"] <= 0:
        raise ValueError("walltime_per_simulation shoulb be > 0")


def validate_data_info(data_info, simul_type):
    keys = ["stationfolder", "total_eventfile", "specfemdir"]
    if simul_type in ["source_inversion", "forward_simulation"]:
        keys.extend(["cmtfolder"])
    elif simul_type in ["adjoint_simulation"]:
        keys.extend(["linkbase", "adjointfolder"])
    for key in keys:
        if key not in data_info:
            raise ValueError("Key(%s) not in config data_info" % (key))


def validate_user_info(user_info):
    keys = ["email"]
    for key in keys:
        if key not in user_info:
            raise ValueError("Key(%s) not in config user_info" % key)


def validate_config(config):
    """ Validtate config information """
    err = 0

    keys = ["simulation_type", "db_name", "runbase", "job_tag",
            "job_config", "data_info", "user_info"]
    for _key in keys:
        if _key not in config:
            print("Key(%s) missing in config" % (_key))
            err = -1

    _options = ["source_inversion", "forward_simulation",
                "adjoint_simulation"]
    simul_type = config["simulation_type"]
    if simul_type not in _options:
        print("simulation_type(%s) not in %s" % (simul_type, _options))
        err = -1

    if err != 0:
        raise ValueError("Error in config!")

    validate_job_config(config["job_config"])
    validate_user_info(config["user_info"])
    validate_data_info(config["data_info"], simul_type)

    # validate certain simulation types
    if simul_type == "source_inversion":
        validate_config_srcinv(config)
