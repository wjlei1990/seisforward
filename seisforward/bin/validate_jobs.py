#!/usr/bin/env python
"""
Scripts that splits a large eventlist file into subfolders.
For example, you have a eventlist contains 320 events.
and you want to split it into 50 events/per file. There will
be 6 files generated. The first 5 files will have 50 events
while the last will have 20 events.
The output job scripts will be put at "$runbase/jobs"
1) split the eventlist
2) create job sub-folder
3) check specfem3d_globe integrity
"""
from __future__ import print_function, division, absolute_import

import argparse
from seisforward.io import load_config
from seisforward.forward_validator import ForwardValidator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)
    simul_type = config["simulation_type"]

    if simul_type == "forward_simulation":
        vd = ForwardValidator(config)
        vd.run()
    elif simul_type == "source_inversion":
        pass
    elif simul_type == "adjoint_simulation":
        pass
    else:
        raise ValueError("simulation type not recognised!")


if __name__ == "__main__":
    main()
