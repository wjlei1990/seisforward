from __future__ import print_function, division, absolute_import
from subprocess import call
import json
import yaml


def load_config(filename):
    """
    load the config yaml file
    """
    with open(filename) as fh:
        config = yaml.load(fh)
    # validate_config(config)
    return config


def dump_json(content, fn):
    with open(fn, 'w') as fh:
        json.dump(content, fh, indent=2, sort_keys=True)


def dump_yaml(content, filename):
    with open(filename, 'w') as fh:
        yaml.dump(content, fh, indent=2)


def read_txt_into_list(filename):
    with open(filename, "r") as fh:
        return [x.rstrip() for x in fh]


def dump_list_to_txt(content, filename):
    with open(filename, 'w') as f:
        for line in content:
            f.write("%s\n" % line)


def bp_validator(fn):
    """
    Use command bpls to check bp file
    """
    command = "bpls -latv %s &> /tmp/adios.tmp.log" % fn
    code = call(command, shell=True)
    return code


def hdf5_validator(fn):
    """
    Use command hdf5 to check hdf5 file
    """
    command = "h5dump -n %s &> /tmp/hdf5.tmp.log" % fn
    code = call(command, shell=True)
    return code
