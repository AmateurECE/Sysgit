#!/usr/bin/env python3
"""
Implements the Repository object interface
"""
###############################################################################
# NAME:             repository.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      A repository object.
#
# CREATED:          11/19/2018
#
# LAST EDITED:      12/22/2018
###

###############################################################################
# IMPORTS
###

import subprocess
import os

import colors

###############################################################################
# CLASSES
###

class RepositoryInfo:
    """RepositoryInfo
    POPO representing some simple status information about a repository.
    """

    def __init__(self):
        """Initialize a new RepositoryInfo object."""
        self.info = {'S': 0, 'M': 0, '?': 0}

    def getStaged(self):
        """Return 1 if the repository has changes staged for commit."""
        return self.info['S']
    def getUnstaged(self):
        """Return 1 if the repository has changes not staged for commit."""
        return self.info['M']
    def getUntracked(self):
        """Return 1 if the repository has untracked files."""
        return self.info['?']

    def setStaged(self, staged):
        """Set state of staged changes to `staged'"""
        self.info['S'] = staged
    def setUnstaged(self, unstaged):
        """Set state of unstaged changes to `unstaged'"""
        self.info['M'] = unstaged
    def setUntracked(self, untracked):
        """Set state of untracked files to `untracked'"""
        self.info['?'] = untracked

    def getStatusInfo(self):
        """Get a string representing the repository's status."""
        stats = ''
        for key in self.info:
            if self.info[key]:
                stats += key
            else:
                stats += ' '
        return stats

    def getNumberOfKeys(self):
        """Return the number of keys in the repository's state dictionary."""
        return len(self.info.keys())


class Repository:
    """Repository:
    POPO representing a Git repository.
    """

    def __init__(self, path):
        """Initialize a Repository object."""
        self.path = path
        self.repoInfo = RepositoryInfo()

    def status(self, verbose=False):
        """
        Get status of the repository
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
        stats = (colors.red + repoStatus + colors.none + ' '
                 + self.path.replace(os.environ['HOME'], "~"))
        for i in range(0, self.repoInfo.getNumberOfKeys()):
            if repoStatus[i] != ' ':
                return (1, stats)
        return (0, stats)

##############################################################################
