#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import os
import time
import math
import glob
from collections import defaultdict

from . import statusobj
from .io import bp_validator, hdf5_validator, read_txt_into_list, dump_json
from .forward_manager import ForwardManager, check_forward_job


class Error(object):
    """ Local Error Message Class """
    def __init__(self, code, old_status=None, new_status=None, msg=None):
        self.code = code
        self.old_status = old_status
        self.new_status = new_status
        self.msg = msg

    def to_dict(self):
        return {"code": self.code, "old_status": self.old_status,
                "new_status": self.new_status, "msg": self.msg}

    def __repr__(self):
        return "Error(code=%d, old_status=%s, new_status=%s, msg=%s)" \
            % (self.code, self.old_status, self.new_status, self.msg)


def validate_forward_simulation(solver, save_forward, mode=1):
    runbase = solver.runbase

    # check the "OUTPUT_FILES/output_solver.txt"
    output_solver_txt = os.path.join(runbase, "OUTPUT_FILES",
                                     "output_solver.txt")
    err = validate_output_solver_txt(output_solver_txt)
    if err.code != 0:
        return err

    # check the "OUTPUT_FILES/synthetic.h5"
    output_asdf = os.path.join(runbase, "OUTPUT_FILES", "synthetic.h5")
    err = validate_synt_asdf_file(output_asdf, mode=mode)
    if err.code != 0:
        return err.msg

    # check the output wavefield
    if save_forward:
        err = validate_wavefield(runbase, mode=mode)
        if err.code != 0:
            return err

    return Error(0, new_status=statusobj.done, msg="valid")


def validate_output_solver_txt(output_solver_txt):
    err = Error(0)
    if not os.path.exists(output_solver_txt):
        err.code = 1
        err.new_status = statusobj.file_not_found
        err.msg = "Missing OUTPUT_FILES/output_solver.txt"
        return err

    # check no NAN values in output_solver.txt. If there are,
    # then the simulation failed.
    unstable_flag = False
    content = read_txt_into_list(output_solver_txt)
    checkpoint = 0
    for line in content:
        if "Max of strain, eps_trace_over_3_crust_mantle" in line:
            v = float(line.split()[-1])
            if math.isnan(v) or math.isinf(v):
                unstable_flag = True
            checkpoint += 1
        if "Max of strain, epsilondev_crust_mantle" in line:
            v = float(line.split()[-1])
            if math.isnan(v) or math.isinf(v):
                unstable_flag = True
            checkpoint += 1

    if unstable_flag:
        err.code = 1
        err.new_status = statusobj.unstable_simulation
        err.msg = "Unstable simulation with NAN or INF values"
        return err

    if "End of the simulation" not in content[-2]:
        err.code = 1
        err.new_status = statusobj.unfinished_simulation
        err.msg = "Unfinished simulation"
        return err

    if checkpoint < 2:
        err.code = 1
        err.new_status = statusobj.unfinished_simulation
        err.msg = "Less than 2 checkpoint found in output_solver.txt"
        return err

    return Error(0, new_status=statusobj.done, msg="valid")


def validate_synt_asdf_file(output_asdf, mode=1):
    """ check output asdf file """
    err = Error(0)
    if not os.path.exists(output_asdf):
        err.code = 1
        err.new_status = statusobj.file_not_found
        err.msg = "Missing output asdf file"
        return err

    if mode == 2:
        _t = time.time()
        code = hdf5_validator(output_asdf)
        if code != 0:
            err.code = 1
            err.new_status = statusobj.invalid_file
            err.msg = "hdf5 validator failed"
        hdf5_t = time.time() - _t
        print("ASDF file(hdf5) validate time: %.1f" % hdf5_t)
        return err

    return Error(0, new_status=statusobj.done, msg="valid")


def validate_wavefield(runbase, mode=1):
    """ check saved wavefields """
    err = Error(0)
    wavefields = glob.glob(os.path.join(runbase, "DATABASES_MPI",
                                        "save_frame_at*.bp"))
    wavefields.sort()
    if len(wavefields) != 26:
        err.code = 1
        err.new_status = statusobj.invalid_file
        err.msg = "Not enough forward wavefiled files: %d < %d" % (
            len(wavefields), 26)
        return err

    if mode == 2:
        _t = time.time()
        code = bp_validator(wavefields[-1])
        if code != 0:
            err.code = 1
            err.new_status = statusobj.invalid_file
            err.msg = "bp validator failed"
        bp_t = time.time() - _t
        print("model files(bp) time:  %.1f" % bp_t)
        return err

    return Error(0, new_status=statusobj.done, msg="valid")


class ForwardValidator(ForwardManager):
    """
    External validator to validate the jobs and change status in
    the table.
    """
    def run(self, mode=1):
        """
        mode 1: checks the existence of synthetic.h5
        """
        status = check_forward_job(self.config["runbase_info"]["db_name"])

        log = {}
        for _s in status:
            _log = self.check_certain_job_status(_s, mode=mode)
            log[_s] = _log

        outputfn = "job_validator.log.json"
        print("Log file: %s" % outputfn)
        dump_json(log, outputfn)

    def check_certain_job_status(self, job_status, mode=1):
        entries = self.fetch_with_status(job_status)
        print("=" * 20)
        print("Number of items(%s): %d" % (job_status, len(entries)))

        before = defaultdict(lambda: 0)
        after = defaultdict(lambda: 0)
        log = []

        save_forward = self.config["simulation"]["save_forward"]
        for solver, _ in entries:
            before[solver.status] += 1
            # print("Solver: %s" % solver)
            _err = validate_forward_simulation(solver, save_forward, mode=mode)
            _err.old_status = solver.status
            _log = _err.to_dict()
            _log["runbase"] = solver.runbase
            log.append(_log)
            solver.status = _err.new_status
            after[solver.status] += 1
            # print("new status: %s" % solver.status)

        print("status before: %s" % before)
        print("status after:  %s" % after)
        self.update_with_status(entries)

        return log
