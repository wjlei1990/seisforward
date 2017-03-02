from __future__ import print_function, division, absolute_import

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class SolverStatus(Base):

    __tablename__ = "status"

    name = Column(String(30), primary_key=True)

    def __repr__(self):
        return "<Status(%s)>" % self.name


class Event(Base):

    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    eventname = Column(String, unique=True)
    cmtfile = Column(String, unique=True)

    solver = relationship("Solver", uselist=False, back_populates="event")
    adjoint_solver = relationship("AdjointSolver", uselist=False,
                                  back_populates="event")

    def __repr__(self):
        return "<Event(eventname='%s', cmtfile='%s')>" % (
            self.eventname, self.cmtfile)


class Solver(Base):
    """
    Solver for forward simulation
    """

    __tablename__ = 'solver'

    id = Column(Integer, primary_key=True)
    stationfile = Column(String)
    runbase = Column(String, unique=True)
    status = Column(String, ForeignKey('status.name'))
    # user defined tag(in line search jobs, it can be perturbation
    # values so it helps to group jobs with the same perturbation
    # values)
    tag = Column(String)

    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship("Event", back_populates="solver")

    def __repr__(self):
        return "<Solver(stationfile='%s', runbase='%s', " \
            "status='%s', tag='%s')>" % (
                self.stationfile, self.runbase, self.status,
                self.tag)


class AdjointSolver(Base):
    """
    Solver for adjoint simulation
    """

    __tablename__ = 'adjointsolver'

    id = Column(Integer, primary_key=True)
    stationfile = Column(String)
    adjointfile = Column(String)
    runbase = Column(String, unique=True)
    status = Column(String, ForeignKey('status.name'))

    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship("Event", back_populates="adjoint_solver")

    def __repr__(self):
        return "<AdjointSolver(eventid=%d, stationfile='%s', " \
            "adjointfile='%s', status=%s)>" \
            % (self.event_id, self.stationfile, self.adjointfile, self.status)
