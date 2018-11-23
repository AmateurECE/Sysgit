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
# LAST EDITED:      11/23/2018
###

###############################################################################
# IMPORTS
###

import subprocess
import colors

###############################################################################
# CLASSES
###

class RepositoryInfo:
    """RepositoryInfo
    POPO representing some simple status information about a repository.
    """
    def __init__(self):
        self.info = {'S': 0, 'M': 0, '?': 0}

    def getStaged(self):
        return self.info['S']
    def getUnstaged(self):
        return self.info['M']
    def getUntracked(self):
        return self.info['?']

    def setStaged(self, staged):
        self.info['S'] = staged
    def setUnstaged(self, unstaged):
        self.info['M'] = unstaged
    def setUntracked(self, untracked):
        self.info['?'] = untracked

    def getStatusInfo(self):
        stats = ''
        for key in self.info:
            if self.info[key]:
                stats += key
            else:
                stats += ' '
        return stats
    def getNumberOfKeys(self):
        return len(self.info.keys())


class Repository:
    """Repository:
    POPO representing a Git repository.
    """
    def __init__(self, path):
        self.path = path
        self.repoInfo = RepositoryInfo()

    def status(self, verbose=False):
        """
        Get status of repository
        """
        cmd = ('git --git-dir=X/.git --work-tree=X status'
               ' --ignore-submodules'
               ' --short')
        cmd = cmd.replace('X', self.path)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        pipe.wait()
        if pipe.returncode != 0:
            raise SystemError('git did not exit successfully.')
        else:
            for line in pipe.stdout.readlines():
                line = line.decode('utf-8').split(' ')
                if line[0] and '?' not in line[0]:
                    self.repoInfo.setStaged(1)
                if (len(line[0]) > 1 and '?' not in line[0]) \
                   or (not line[0] and line[1]):
                    self.repoInfo.setUnstaged(1)
                elif '?' in line[0]:
                    self.repoInfo.setUntracked(1)

        # Set the fields in the string
        repoStatus = self.repoInfo.getStatusInfo()
        stats = colors.red + repoStatus + colors.none + ' ' + self.path
        for i in range(0, self.repoInfo.getNumberOfKeys()):
            if repoStatus[i] is not ' ':
                return (1, stats)
        return (0, stats)

    def info(self, verbose=False):
        """
        Get more detailed info on a particular repository.
        """
        # TODO: Stabilize Repository.info()
        self.status(verbose)

##############################################################################
