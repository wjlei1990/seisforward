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
from seisforward.forward_manager import ForwardSolver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    args = parser.parse_args()

    manager = ForwardSolver(config=args.config_file)
    manager.create_jobs()


if __name__ == "__main__":
    main()
