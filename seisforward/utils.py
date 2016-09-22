#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import os
import sys
import glob
import shutil
import time


def timer(func):
    def timed(*args, **kws):
        ts = time.time()
        result = func(*args, **kws)
        te = time.time()

        print("func [%s] took: %2.4f sec" % (func.__name__, te-ts))
        return result
    return timed


def safe_makedir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def check_exist(filename):
    if not os.path.exists(filename):
        raise ValueError("Path not exists: %s" % filename)


def cleantree(folder):
    if not os.path.exists(folder):
        return
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception, e:
            print(e)


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(src):
        raise ValueError("Src dir not exists: %s" % src)
    if not os.path.exists(dst):
        raise ValueError("Dest dir not exists: %s" % dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def copyfile(origin_file, target_file, verbose=True):
    if not os.path.exists(origin_file):
        raise ValueError("No such file: %s" % origin_file)

    if not os.path.exists(os.path.dirname(target_file)):
        os.makedirs(os.path.dirname(target_file))

    if verbose:
        print("Copy file:[%s --> %s]" % (origin_file, target_file))
    shutil.copy2(origin_file, target_file)


def get_permission():
    answer = raw_input("[Y/n]:")
    if answer == "Y":
        return True
    elif answer == "n":
        return False
    else:
        raise ValueError("answer incorrect: %s" % answer)


def check_folders_exist(targetdir_list):
    clean_status = 1
    for targetdir in targetdir_list:
        if os.path.exists(targetdir):
            print("job folder exists: %s" % targetdir)
            clean_status = 0

    if clean_status == 0:
        print("Removed?")
        if get_permission():
            for _dir in targetdir_list:
                if os.path.exists(_dir):
                    cleantree(_dir)
        else:
            sys.exit(0)


def get_package_path():
    import seisforward
    return seisforward.__path__[0]


def safe_remove(_dir):
    if os.path.isdir(_dir):
        if os.path.islink(_dir):
            os.unlink(_dir)
        else:
            shutil.rmtree(_dir)
    else:
        if os.path.islink(_dir):
            os.unlink(_dir)
        else:
            shutil.remove(_dir)


def clean_specfem(specfemdir):
    """
    Clean run**** from specfem directory
    """
    # clean previous run_**** first
    dirlist = glob.glob(os.path.join(specfemdir, "run*"))
    print("remove dirlist: ", dirlist)
    for _dir in dirlist:
        safe_remove(_dir)


def make_title(text, symbol="=", symbol_len=10, space_len=3):
    total_len = len(text) + symbol_len * 2 + space_len * 2
    string = symbol * total_len + "\n"
    string += symbol * symbol_len + " " * space_len + text + \
        " " * space_len + symbol * symbol_len + "\n"
    string += symbol * total_len
    return string
