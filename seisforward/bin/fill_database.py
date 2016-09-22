import os
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from seisforward.status import Status
from seisforward.db import Event, Solver
from seisforward.io import load_config, read_txt_into_list
from seisforward.validate_config import validate_config


def fill_forward_db(config, verbose=False):
    db_name = config["db_name"]
    runbase = config["runbase"]

    cmtfolder = config["data_info"]["cmtfolder"]
    stationfolder = config["data_info"]["stationfolder"]

    print("Filling database: %s" % db_name)
    print("=" * 20)
    print("Runbase: %s" % runbase)
    print("cmtfolder: %s" % cmtfolder)
    print("stationfolder:%s" % stationfolder)

    eventfile = config["data_info"]["total_eventfile"]
    events = read_txt_into_list(eventfile)
    nevents = len(events)
    print("eventfile: %s" % eventfile)
    print("Number of events: %s" % nevents)

    engine = create_engine('sqlite:///%s' % db_name, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    for idx, eventname in enumerate(events):
        cmtfile = os.path.join(cmtfolder, eventname)
        stationfile = os.path.join(stationfolder, "STATIONS.%s" % eventname)
        entry_rundir = os.path.join(runbase, "archive", eventname)

        if verbose:
            print("-" * 5 + " [%d/%d]%s " % (idx+1, nevents, eventname) +
                  "-" * 5)
            print("cmtfile: %s\nstationfile: %s\nentry_rundir: %s"
                  % (cmtfile, stationfile, entry_rundir))

        eventobj = Event(eventname=eventname,
                         cmtfile=cmtfile)
        solver = Solver(stationfile=stationfile,
                        runbase=entry_rundir,
                        status=Status().new)
        print(solver)
        solver.event = eventobj
        session.add(solver)

    session.commit()
    session.close()


def fill_adjoint_db(config, verbose=False):
    raise NotImplementedError("Not implemented yet with adjoint")


def fill_srcinv_db(config, verbose=False):
    raise NotImplementedError("Not implemented yet with source inversion")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help="verobse flag")
    args = parser.parse_args()

    config = load_config(args.config_file)
    validate_config(config)

    simul_type = config["simulation_type"]
    print("Simulation type: %s" % simul_type)
    if simul_type == "adjoint_simulation":
        fill_adjoint_db(config, verbose=args.verbose)
    elif simul_type == "forward_simulation":
        fill_forward_db(config, verbose=args.verbose)
    elif simul_type == "source_inversion":
        fill_srcinv_db(config, verbose=args.verbose)
    else:
        raise ValueError("Unsupported simulation type(%s)" % simul_type)


if __name__ == "__main__":
    main()
