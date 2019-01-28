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
# class RepositoryInfo
###

class RepositoryInfo:
    """RepositoryInfo
    POPO representing some simple status information about a repository.
    """

    def __init__(self):
        """Initialize a new RepositoryInfo object."""
        self.workingTreeInfo = {'S': 0, 'M': 0, '?': 0}

    def getStaged(self):
        """Return 1 if the repository has changes staged for commit."""
        return self.workingTreeInfo['S']
    def getUnstaged(self):
        """Return 1 if the repository has changes not staged for commit."""
        return self.workingTreeInfo['M']
    def getUntracked(self):
        """Return 1 if the repository has untracked files."""
        return self.workingTreeInfo['?']

    def setStaged(self, staged):
        """Set state of staged changes to `staged'"""
        self.workingTreeInfo['S'] = staged
    def setUnstaged(self, unstaged):
        """Set state of unstaged changes to `unstaged'"""
        self.workingTreeInfo['M'] = unstaged
    def setUntracked(self, untracked):
        """Set state of untracked files to `untracked'"""
        self.workingTreeInfo['?'] = untracked

    def getStatusStringLength(self):
        """Get the length of the string returned by getWorkingTreeStatus"""
        return len(self.workingTreeInfo)

    def getStatus(self):
        """Get a string representing the repository's status."""
        stats = ''
        for key in self.workingTreeInfo:
            if self.workingTreeInfo[key]:
                stats += key
            else:
                stats += ' '
        return stats

###############################################################################
# Repository
###

class Repository:
    """Repository:
    Class representing a Git repository.
    """

    def __init__(self, workTree, gitDir=None):
        """Initialize a Repository object."""
        self.workTree = workTree
        if gitDir is None:
            self.gitDir = workTree + '/.git'
        else:
            self.gitDir = gitDir
        self.repoInfo = RepositoryInfo()
        self.submoduleUTD = False
        self.workingTreeUTD = False
        self.hasChanges = False
        self.submodules = list()

    def status(self, stats, submodules=False, begin='', color=True):
        """
        PUBLIC. Get status of the repository
        """
        # populateWorkingTreeInfo populates self.repoInfo as a side effect
        if not self.workingTreeUTD:
            self.populateWorkingTreeInfo()
        # When support is added for remote branches, it needs to go here.
        if submodules and not self.submoduleUTD:
            self.populateSubmoduleInfo()
        if not self.hasChanges:
            return (self.hasChanges, '')

        stats = self.makeSummaryString(stats, submodules=submodules,
                                       begin=begin, color=color)
        return (self.hasChanges, stats)

    def makeSummaryString(self, stats, submodules=False, begin='', color=True):
        """
        INTERNAL. Performs string operations to generate the status string that
        might get printed by the caller. This method treats `stats' like a
        terminal object.
        """
        repoPath = self.workTree.replace(os.environ['HOME'], "~")
        if repoPath[len(repoPath) - 1] == '/':
            repoPath = repoPath[:-1]
        # Put together the status string for THIS repository
        if color:
            stats = (stats + colors.red + self.repoInfo.getStatus()
                     + colors.none + ' ' + repoPath + '\n')
        else:
            stats = (stats + self.repoInfo.getStatus() + ' ' + repoPath + '\n')
        # Do (ERE) 's#//+#/#g'
        stats = '/'.join(filter(None, stats.split('/'))) # s'#//\+##g'
        # Put together the status string for submodules
        if submodules:
            for module in self.submodules:
                submoduleStatus = begin + '\t'
                changes, submoduleStatus = module.status(submoduleStatus,
                                                         submodules=True,
                                                         begin=begin + '\t')
                if changes:
                    stats = (stats + submoduleStatus.replace(repoPath, ''))
        return stats

    def populateWorkingTreeInfo(self):
        """
        INTERNAL. Execute Git commands to populate the workingTreeInfo member
        of this RepositoryInfo object.
        """
        cmd = ('git --git-dir=xGD --work-tree=xWT status'
               ' --ignore-submodules'
               ' --short')
        pipe = self.executeGitCommand(cmd.replace('xGD', self.gitDir)
                                      .replace('xWT', self.workTree))

        # Parse the output and populate the fields.
        for line in pipe.stdout.readlines():
            line = line.decode('utf-8').split(' ')
            if line[0] and '?' not in line[0]:
                self.repoInfo.setStaged(1)
                self.hasChanges = True
            if (len(line[0]) > 1 and '?' not in line[0]) \
               or (not line[0] and line[1]):
                self.repoInfo.setUnstaged(1)
                self.hasChanges = True
            elif '?' in line[0]:
                self.repoInfo.setUntracked(1)
                self.hasChanges = True

        self.workingTreeUTD = True
        return self.hasChanges

    def populateSubmoduleInfo(self):
        """INTERNAL. Execute Git commands to populate self.submodules"""
        entries = self.parseGitmodules(self.workTree + '/.gitmodules')
        for entry in entries:
            # Instantiate the submodule
            submodule = Repository(workTree=(self.workTree + '/'
                                             + entry['path']),
                                   gitDir=(self.gitDir + '/modules/'
                                           + entry['name']))
            if submodule.populateWorkingTreeInfo():
                self.hasChanges = True
            if submodule.populateSubmoduleInfo():
                self.hasChanges = True
            self.submodules.append(submodule)

        self.submoduleUTD = True
        return self.hasChanges

    @staticmethod
    def parseGitmodules(path):
        """INTERNAL. Parse the .gitmodules file @ path into a list of dicts."""
        entries = list()
        try:
            with open(path, 'r') as gitmodules:
                # Parse the .gitmodules file.
                lines = gitmodules.readlines()
                try:
                    while lines:
                        line = lines.pop(0)
                        while line[0] != '[':
                            line = lines.pop(0)

                        # Get the module name
                        moduleName = line.split('"')[1]

                        line = lines.pop(0)
                        # Get the module path
                        modulePath = ''
                        while line[0] in (' ', '\t'):
                            pieces = line.split()
                            if pieces[0] == 'path':
                                modulePath = pieces[2]
                                break
                            line = lines.pop(0)

                        # Create the entry
                        entries.append({'name': moduleName,
                                        'path': modulePath})
                except IndexError:
                    pass
        except FileNotFoundError:
            pass
        return entries

    @staticmethod
    def executeGitCommand(cmd):
        """INTERNAL. Spawns a subprocess to execute a git command"""
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        pipe.wait()
        if pipe.returncode != 0:
            raise SystemError('git did not exit successfully.')
        return pipe

##############################################################################
