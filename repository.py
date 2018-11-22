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

import colors

###############################################################################
# CLASSES
###

class Repository:
    """Repository:
    POPO representing a Git repository.
    """
    def __init__(self, path):
        self.path = path
        self.info = {'S': 0, 'M': 0, 'U': 0}

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
                line = line.decode('utf-8')
                if 'committed' in line:
                    self.info['S'] = 1
                elif 'not staged' in line:
                    self.info['M'] = 1
                elif 'Untracked' in line:
                    self.info['U'] = 1

        # Set the fields in the string
        stats = colors.red
        for key in self.info.keys():
            if self.info[key]:
                stats += key
            else:
                stats += ' '

        stats += colors.none
        stats += ' '
        stats += self.path
        if self.info['S'] or self.info['M'] or self.info['U']:
            return (1, stats)
        else:
            return (0, stats)

    def info(self, verbose=False):
        """
        Get more detailed info on a particular repository.
        """
        # TODO: Stabilize Repository.info()
        self.status(verbose)

##############################################################################
