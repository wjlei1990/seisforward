import os
import glob
import re
from .utils import read_txt_into_list


def fortran_bool(string):
    if re.search('false', string, re.IGNORECASE):
        return False
    elif re.search('true', string, re.IGNORECASE):
        return True
    else:
        return None


def check_specfem(specfemdir):
    print("============= Checking SPECFEM3D_GLOBE ============")
    check_specfem_common(specfemdir)
    check_specfem_model(specfemdir)

    parfile = os.path.join(specfemdir, "DATA", "Par_file")
    check_specfem_parfile(parfile)


def check_specfem_common(specfemdir):
    filelist = ["bin/xspecfem3D", "OUTPUT_FILES/addressing.txt",
                "OUTPUT_FILES/values_from_mesher.h",
                "DATA/Par_file"]

    for _file in filelist:
        path = os.path.join(specfemdir, _file)
        if not os.path.exists(path):
            raise ValueError("File not exists: %s" % (path))


def check_specfem_model(specfemdir):
    print("-"*10 + " Checking SPECFEM model file " + "-"*10)
    # check model file
    path = os.path.join(specfemdir, "DATABASES_MPI")
    bpfiles = glob.glob(os.path.join(path, "*.bp"))
    binfiles = glob.glob(os.path.join(path, "*.bin"))
    print("Number of bp files:%d: and number of bin files:%d:"
          % (len(bpfiles), len(binfiles)))
    if len(bpfiles) == 4:
        if len(binfiles) != 1:
            raise ValueError("Check model files: %s" % path)
    elif len(bpfiles) == 0:
        if len(binfiles) <= 2:
            raise ValueError("Check model files: %s" % path)
        else:
            print("Number of model bin files: %d" % len(binfiles))
    else:
        raise ValueError("Check model files: %s" % path)


def check_specfem_parfile(parfile_path):
    content = read_txt_into_list(parfile_path)
    for line in content:
        if re.search(r'^SIMULATION_TYPE(\s*)=', line):
            stype = int(line.split()[2])
        if re.search(r'^SAVE_FORWARD(\s*)=', line):
            save_forward = fortran_bool(line.split()[2])
        if re.search(r'NCHUNKS(\s*)=', line):
            nchunks = int(line.split()[2])
        if re.search(r'^NEX_XI(\s*)=', line):
            nex_xi = int(line.split()[2])
        if re.search(r'^NEX_ETA(\s*)=', line):
            nex_eta = int(line.split()[2])
        if re.search(r'^NPROC_XI(\s*)=', line):
            nproc_xi = int(line.split()[2])
        if re.search(r'^NPROC_ETA(\s*)=', line):
            nproc_eta = int(line.split()[2])
        if re.search(r'^MODEL(\s*)=', line):
            model = line.split()[2]
        if re.search(r'^ATTENUATION(\s*)=', line):
            attenuation = fortran_bool(line.split()[2])
        if re.search(r'^ABSORBING_CONDITIONS(\s*)=', line):
            absorb_cond = fortran_bool(line.split()[2])
        if re.search(r'^RECORD_LENGTH_IN_MINUTES(\s*)=', line):
            record_length = float(line.split()[2].split("d")[0])
        if re.search(r'^PARTIAL_PHYS_DISPERSION_ONLY(\s*)=', line):
            partial_phys_disp = fortran_bool(line.split()[2])
        if re.search(r'^UNDO_ATTENUATION(\s*)=', line):
            undo_att = fortran_bool(line.split()[2])
        if re.search(r'^BROADCAST_SAME_MESH_AND_MODEL(\s*)=', line):
            broadcast = fortran_bool(line.split()[2])
        if re.search(r'^GPU_MODE(\s*)=', line):
            gpu_mode = fortran_bool(line.split()[2])
        if re.search(r'^ADIOS_ENABLED(\s*)=', line):
            adios_enabled = fortran_bool(line.split()[2])

    # print summary
    print("-"*10 + " Checking SPECFEM Par_file " + "-"*10)
    print("Simulation_type: %d  Save_Forward: %s" % (stype, save_forward))
    print("nchunks, absorbing condition: \t%d, %s" % (nchunks, absorb_cond))
    print("NEX_XI and NEX_ETA: \t\t(%d, %d)\n"
          "NPROC_XI and NPROC_ETA: \t(%d, %d)"
          % (nex_xi, nex_eta, nproc_xi, nproc_eta))
    print("Model: \t\t\t\t%s" % model)
    print("attenuation: \t\t\t%s" % attenuation)
    print("phys dispersion and undo att: \t%s, %s"
          % (partial_phys_disp, undo_att))
    print("Broadcast model and mesh: \t%s" % broadcast)
    print("GPU mode and ADIOS: \t\t%s, %s" % (gpu_mode, adios_enabled))

    err = 0
    #if stype == 1:
    #    if not save_forward:
    #        print("Error: Forward simulation must save_forward")
    #        err = 1
    #elif stype == 3:
    #    if save_forward:
    #        print("Error: Adjoint simulation can't save_forward")
    #        err = 1
    #else:
    #    print("Error: Unrecongnized simulation_type(%d)" % stype)
    #    err = 1

    if nchunks != 6:
        print("Error: nchunks is not 6")
        err = 1

    if nex_xi % (8*nproc_xi) != 0 or nex_eta % (8*nproc_eta) != 0:
        print("Error: Check your NEX_XI, NEX_ETA, NPROC_XI, NPROC_ETA"
              "settings")
        err = 1

    if model != "GLL":
        print("Error: MODEL must be 'GLL'")
        err = 1

    if not attenuation:
        print("Error: attenuation must True")
        err = 1

    if absorb_cond:
        print("Error: global simulation must set absorbing_condition to"
              " False")
        err = 1

    if record_length < 30.0:
        print("Error: record_lenght_in_minutes is shorter than 60 min")
        err = 1

    if partial_phys_disp:
        print("Error: Partial physical dispersion must be False")
        err = 1

    if not undo_att:
        print("Error: undo_attenuation must be true")
        err = 1

    if not broadcast:
        print("Error: broadcast model and mesh must be True")
        err = 1

    if not gpu_mode:
        print("Error: GPU_MODE must be True")
        err = 1

    if not adios_enabled:
        print("ADIOS mode must be True")
        err = 1

    if err == 1:
        raise ValueError("Error in Par_file of specfem3d_globe")
