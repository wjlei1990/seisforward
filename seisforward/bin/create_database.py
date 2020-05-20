#!/bin/usr/env python

# create database
from __future__ import print_function, division, absolute_import
import os
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from seisforward.status import Status
from seisforward.db import Base, SolverStatus
from seisforward.io import load_config


def create_forward_db(db_name, verbose=False):
    """
    Create the empty database
    """
    if os.path.exists(db_name):
        raise ValueError("Database(%s) already exists!" % (db_name))

    engine = create_engine('sqlite:///%s' % db_name, echo=verbose)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    statuses = Status().get_status()
    for s in statuses:
        statusobj = SolverStatus(name=s)
        session.add(statusobj)

    session.commit()
    session.close()


def check_db_exists(db_name):
    """
    Check the existence of database(use the same one as forward simulation)
    Since adjoint simulation just need two more extra files,
    DATA/STATIONS_ADJOINT and SEM/adjoint.h5, copied to the event dir.
    So there is no need to build up a new database.
    """
    if not os.path.exists(db_name):
        raise ValueError("Database for adjoint runs not exists: %s"
                         % db_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store', dest='config_file',
                        required=True, help="config yaml file")
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help="verobse flag")
    args = parser.parse_args()

    config = load_config(args.config_file)

    stype = config["simulation"]["type"]
    db_name = config["runbase_info"]["db_name"]

    if stype == "forward_simulation" or "line_search":
        create_forward_db(db_name, args.verbose)
    elif stype == "adjoint_simulation":
        check_db_exists(db_name)


if __name__ == "__main__":
    main()
