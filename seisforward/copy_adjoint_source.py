import os
import shutil
from .utils import safe_makedir


def copy_adjoint_source(eventlist, adjointdir, archivedir):
    idx = 0
    nevents = len(eventlist)
    print("Number of events: %d" % nevents)
    print("Adjoint file dir: %s" % adjointdir)
    print("Archive(dest) dir: %s" % archivedir)
    for idx, event in enumerate(eventlist):
        event_dir = os.path.join(archivedir, event)
        if not os.path.exists(event_dir):
            raise ValueError("Adjoint event directory not exists: %s"
                             % event_dir)
        sem_dir = os.path.join(event_dir, "SEM")
        safe_makedir(sem_dir)
        dest_fn = os.path.join(sem_dir, "adjoint.h5")

        adjoint_fn = os.path.join(adjointdir, "%s.adjoint.h5" % event)
        if not os.path.exists(adjoint_fn):
            raise ValueError("No adjoint file: %s" % adjoint_fn)

        print("-" * 10 + "\n[%d/%d]Copy adjoint file: %s --> %s"
              % (idx+1, nevents, adjoint_fn, dest_fn))

        shutil.copy(adjoint_fn, dest_fn)
