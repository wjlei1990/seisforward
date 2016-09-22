#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import argparse
from seisforward.io import load_config
from seisforward.forward_manager import check_forward_job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)
    simul_type = config["simulation_type"]
    db_name = config["db_name"]

    if simul_type == "forward_simulation":
        check_forward_job(db_name)
    elif simul_type == "adjoint_simulation":
        pass
    elif simul_type == "source_inversion":
        pass
    else:
        raise ValueError("Simulation type(%s) not recognised!" % simul_type)


if __name__ == "__main__":
    main()
