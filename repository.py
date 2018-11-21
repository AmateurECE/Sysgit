#!/usr/bin/env python3
###############################################################################
# NAME:             repository.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      A repository object.
#
# CREATED:          11/19/2018
#
# LAST EDITED:      11/21/2018
###

###############################################################################
# IMPORTS
###

import os.path
import subprocess

###############################################################################
# CLASSES
###

class Repository:
    """Repository:
    POPO representing a Git repository.
    """
    def __init__(self, path):
        self.path = os.path.expanduser(path)

    def status(self, verbose=False):
        """
        Get status of repository
        """
        cmd = 'git --git-dir=X/.git --work-tree=X status --ignore-submodules'
        cmd = cmd.replace('X', self.path)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        pipe.wait()
        if pipe.returncode != 0:
            raise SystemError('git did not exit successfully.')
        else:
            for line in pipe.stdout.readlines():
                print(line.decode('utf-8'), end='')

    def info(self, verbose=False):
        """
        Get more detailed info on a particular repository.
        """
        # TODO: Stabilize Repository.info()
        self.status(verbose)

##############################################################################
