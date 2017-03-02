#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import os
import time
import glob
from collections import defaultdict
import shutil
from copy import deepcopy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import statusobj
from .utils import safe_makedir, get_package_path, \
    check_folders_exist, clean_specfem, make_title
from .io import bp_validator, hdf5_validator, load_config, \
    dump_list_to_txt, dump_yaml
from .validate_config import validate_config
from .db import Solver, Event
from .generate_pbs_script import generate_pbs_script, modify_specfem_parfile
from .check_specfem import check_specfem
from .easy_copy_specfem import easy_copy_specfem


def setup_entry_dir(entries, specfemdir):
    """
    Setup the directory for each entry for forward simulation
    1) create directory(DATA, OUTPUT_FILES, DATABASES_MPI)
    2) copy CMTSOLUTION and STATION(forward simulation)
    3) copy values_from_mesher.h and addressing.h
    """
    nentries = len(entries)
    for idx, (solver, event) in enumerate(entries):
        runbase = solver.runbase
        print("[%d/%d] %s --- runbase: %s" % (idx+1, nentries,
                                              event.eventname, runbase))
        safe_makedir(runbase)

        # copy CMTSOLUTION and STATIONS
        targetdir = os.path.join(runbase, "DATA")
        safe_makedir(targetdir)
        cmtfile = event.cmtfile
        shutil.copy(cmtfile, os.path.join(targetdir, "CMTSOLUTION"))
        stationfile = solver.stationfile
        shutil.copy(stationfile, os.path.join(targetdir, "STATIONS"))

        # copy values_from_mesher.h and addressing.h
        targetdir = os.path.join(runbase, "OUTPUT_FILES")
        safe_makedir(targetdir)
        filelist = ["values_from_mesher.h", "addressing.txt"]
        for _file in filelist:
            file1 = os.path.join(specfemdir, "OUTPUT_FILES", _file)
            file2 = os.path.join(targetdir, _file)
            shutil.copy(file1, file2)

        # mkdir DATABASES_MPI, but no files copied at this stage(
        # using symbolic links for model files instead at simulation
        # stage)
        targetdir = os.path.join(runbase, "DATABASES_MPI")
        safe_makedir(targetdir)


def validate_entries(entries):
    """
    validate forward entries. forward entry must have
    1) cmtfile; 2) station file
    """
    err = 0
    for solver, event in entries:
        cmtfile = event.cmtfile
        if not os.path.exists(cmtfile):
            err = -1
            print("Missing cmtfile: %s" % cmtfile)

        stationfile = solver.stationfile
        if not os.path.exists(stationfile):
            err = -1
            print("Missing stationfile: %s" % stationfile)

    if err != 0:
        raise ValueError("Error in db!")


def dump_eventlist(entries, job_dir, n_serial, n_simul):
    """
    dump event list to job dir
    """
    events = [event.eventname for _, event in entries]
    if len(events) != (n_serial * n_simul):
        raise ValueError("Number of events(%d) != (%d * %d)"
                         % (len(events), n_serial, n_simul))

    fn = os.path.join(job_dir, "_XEVENTID.all")
    dump_list_to_txt(events, fn)

    for idx in range(n_serial):
        fn = os.path.join(job_dir, "XEVENTID.%d" % (idx+1))
        start_idx = n_simul * idx
        end_idx = n_simul * (idx + 1)
        dump_list_to_txt(events[start_idx:end_idx], fn)


def create_job_folder(job_dir, entries, config, specfem_base):
    """
    create job folder, to hold XEVENTID.* and pbs script.
    Keep an copy of specfem stuff(excluding the model file because of
    its size) at local dir. So jobs could be submitted inside the job
    dir indepandently.
    """
    print("*"*20 + "\nCreat job sub folders")
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
        "job_solver.%s.bash" % simul_type)
    outputfn = os.path.join(job_dir, "job_solver.bash")
    generate_pbs_script(template, outputfn, config, local_specfem)

    modify_specfem_parfile(config, local_specfem)


def create_db_connection(db_name):
    if not os.path.exists(db_name):
        raise ValueError("No db exists: %s" % db_name)

    engine = create_engine('sqlite:///%s' % db_name, echo=False)
    Session = sessionmaker(bind=engine)
    return engine, Session


class ForwardManager(object):
    """
    Forward simulation manager(mainly DB utilities)
    """
    def __init__(self, config):
        self._load_config(config)

        self.engine, self.Session = \
            create_db_connection(self.config["db_name"])

    def _load_config(self, config):
        if isinstance(config, str):
            # it is the file
            if not os.path.exists(config):
                raise ValueError("Config file(%s) not eixsts!")
            config = load_config(config)

        validate_config(config)
        self.config = deepcopy(config)

    def fetch_with_status(self, status, tag=None, num_to_fetch=None):
        """
        Fetch Solver and Event together from database
        """
        session = self.Session()
        query = session.query(Solver, Event).join(Event).\
            filter(Solver.status == status)

        if tag is not None:
            query = query.filter(Solver.tag == tag)

        query = query.order_by(Solver.id)
        if num_to_fetch is not None and num_to_fetch > 0:
            query = query.limit(num_to_fetch)

        entries = query.all()
        session.close()
        return entries

    def update_with_status(self, entries, status=None):
        """
        Update Solver in entries to status(if given) or from Solver.status
        """
        session = self.Session()
        for solver, _ in entries:
            if status is None:
                session.query(Solver).filter(Solver.id == solver.id).\
                    update({'status': solver.status})
            else:
                session.query(Solver).filter(Solver.id == solver.id).\
                    update({'status': status})

        session.commit()
        session.close()

    def retrieve_new_entries_from_db(self, tag=None, num_to_fetch=None):
        job_entries = []
        while True:
            entries = self.fetch_with_status(
                statusobj.new, tag=tag, num_to_fetch=num_to_fetch)
            if len(entries) < num_to_fetch:
                break
            validate_entries(entries)
            self.update_with_status(entries, status=statusobj.ready_to_launch)
            job_entries.append(entries)

        return job_entries


class ForwardSolver(ForwardManager):
    """
    Forward job creator
    """
    def get_new_entries(self):
        print(make_title("Retrieve jobs from DB"))
        n_serial = self.config["job_config"]["n_serial"]
        n_simul = self.config["job_config"]["nevents_per_simul_run"]
        num_to_fetch = n_serial * n_simul
        print("n_serial * n_simul = n_total: %d * %d = %d"
              % (n_serial, n_simul, num_to_fetch))

        runbase = self.config["runbase"]
        job_entries = self.retrieve_new_entries_from_db(
            num_to_fetch=num_to_fetch)
        job_base = os.path.join(runbase, "jobs")
        njobs = len(job_entries)
        print("Number of jobs: %d" % njobs)

        job_prefix = self.config["job_folder_prefix"]
        job_dirs = [
            os.path.join(job_base, "job_%s_%02d" % (job_prefix, idx+1))
            for idx in range(njobs)]
        check_folders_exist(job_dirs)
        return job_dirs, job_entries

    def create_jobs(self):
        config = self.config

        runbase = config["runbase"]
        specfem_base = os.path.join(runbase, "specfem3d_globe")
        check_specfem(specfem_base)

        job_dirs, job_entries = self.get_new_entries()

        njobs = len(job_entries)
        idx = 0
        for _dir, _entries in zip(job_dirs, job_entries):
            idx += 1
            print(make_title("Create job[%d/%d]" % (idx, njobs)))
            print("job dir: %s" % _dir)
            print("Number of entries: %d" % len(_entries))
            setup_entry_dir(_entries, specfem_base)
            create_job_folder(_dir, _entries, config, specfem_base)


class ForwardValidator(ForwardManager):
    """
    External validator to validate the jobs and change status in
    the table.
    """
    def run(self, mode=1):
        """
        mode 1: checks the existence of synthetic.h5 and
        """
        check_forward_job(self.config["db_name"])

        self.check_certain_job_status(statusobj.ready_to_launch, mode=mode)
        self.check_certain_job_status(statusobj.done, mode=mode)
        self.check_certain_job_status(statusobj.file_not_found, mode=mode)

    def check_certain_job_status(self, job_status, mode=1):
        entries = self.fetch_with_status(job_status)
        print("=" * 20)
        print("Number of items(%s): %d" % (job_status, len(entries)))

        before = defaultdict(lambda: 0)
        after = defaultdict(lambda: 0)
        for solver, _ in entries:
            before[solver.status] += 1
            # print("Solver: %s" % solver)
            self.validate(solver, mode=mode)
            after[solver.status] += 1
            # print("new status: %s" % solver.status)

        print("status before: %s" % before)
        print("status after:  %s" % after)
        self.update_with_status(entries)

    @staticmethod
    def validate(solver, mode=1):
        runbase = solver.runbase

        # check output asdf file
        output_asdf = os.path.join(runbase, "OUTPUT_FILES", "synthetic.h5")
        if not os.path.exists(output_asdf):
            solver.status = statusobj.file_not_found
            return

        if mode == 2:
            _t = time.time()
            code = hdf5_validator(output_asdf)
            if code != 0:
                solver.status = statusobj.invalid_file
                return
            hdf5_t = time.time() - _t
            print("ASDF file(hdf5) validate time: %.1f" % hdf5_t)

        # check saved wavefields
        wavefields = glob.glob(os.path.join(runbase, "DATABASES_MPI",
                                            "save_frame_at*.bp"))
        wavefields.sort()
        if len(wavefields) != 26:
            solver.status = statusobj.file_not_found
            return

        if mode == 2:
            _t = time.time()
            code = bp_validator(wavefields[-1])
            if code != 0:
                solver.status = statusobj.invalid_file
                return
            bp_t = time.time() - _t
            print("model files(bp) time:  %.1f" % bp_t)

        solver.status = statusobj.done


def reset_forward_job(db_name):
    """
    reset forward table entries, whose status is not "Done" to "New"
    so jobs could be re-fetched and re-launched later
    """
    if not os.path.exists(db_name):
        raise ValueError("No db exists: %s" % db_name)

    engine = create_engine('sqlite:///%s' % db_name, echo=False)
    Session = sessionmaker(bind=engine)

    session = Session()
    entries = session.query(Solver).all()
    nresets = 0
    for entry in entries:
        if entry.status != statusobj.done:
            nresets += 1
            entry.status = statusobj.new

    session.commit()
    session.close()
    print("Reset entries to new: %d/%d" % (nresets, len(entries)))


def check_forward_job(db_name):
    """
    check and stats the status of forward jobs in the forward table.
    """
    if not os.path.exists(db_name):
        raise ValueError("No db exists: %s" % db_name)

    engine = create_engine('sqlite:///%s' % db_name, echo=False)
    Session = sessionmaker(bind=engine)

    session = Session()
    entries = session.query(Solver).all()
    session.close()

    results = {}
    for entry in entries:
        if entry.status not in results:
            results[entry.status] = 0
        results[entry.status] += 1

    print("Current status in Forward tables: %s" % results)
