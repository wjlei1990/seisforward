from __future__ import print_function, division, absolute_import


class Status(object):
    def __init__(self):
        self.new = "New"
        self.done = "Done"
        self.ready_to_launch = "ReadytoLaunch"
        self.queued = "Queued"
        self.failed = "Failed"
        self.running = "Running"
        self.file_not_found = "FileNotFound"
        self.invalid_file = "InvalidFile"

    def get_status(self):
        return sorted(self.__dict__.values())
