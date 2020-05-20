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
from seisforward.forward_manager import ForwardSolver
from seisforward.line_search_manager import LineSearchSolver


def create_forward_jobs(config):
    manager = ForwardSolver(config=config)
    manager.create_jobs()


def create_adjoint_jobs(config):
    raise NotImplementedError("adjoint not implemented yet!")


def create_line_search_jobs(config):
    manager = LineSearchSolver(config=config)
    manager.create_jobs()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    config = load_config(args.config_file)

    stype = config["simulation"]["type"]
    if stype == "forward_simulation":
        create_forward_jobs(config)
    elif stype == "adjoint_simulation":
        create_adjoint_jobs(config)
    elif stype == "line_search":
        create_line_search_jobs(config)
    else:
        raise NotImplementedError("Error: %s" % stype)


if __name__ == "__main__":
    main()
