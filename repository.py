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

import colors as TerminalColors

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
        self.bugs = False
        self.changes = False

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

    def setBugs(self, bugs):
        """Set state of repository's bugs file."""
        self.bugs = bugs
    def getBugs(self):
        """Return state of repository's bugs file."""
        return self.bugs

    def setChanges(self, hasChanges):
        """Set status of repository's hasChanges flag."""
        self.changes = hasChanges
    def hasChanges(self):
        """Return status of repository's hasChanges flag."""
        return self.changes

    def getStatusStringLength(self):
        """Get the length of the string returned by getWorkingTreeStatus"""
        return len(self.workingTreeInfo)

    def getBugStatus(self):
        """Get a string representing the status of the bugs file."""
        if self.bugs:
            return 'B'
        return ' '

    def getStatus(self):
        """Get a string representing the repository's working tree status."""
        stats = ''
        for key in self.workingTreeInfo:
            if self.workingTreeInfo[key]:
                stats += key
            else:
                stats += ' '
        return stats

###############################################################################
# class RepositoryFlags
###

class RepositoryFlags:
    """Container for data that dictates the format of the status string."""

    def __init__(self, submodules=False, bugs=False, colors=True):
        """Initialize a RepositoryFlags object."""
        self.submodules = submodules
        self.bugs = bugs
        self.colors = colors

    def getSubmodules(self):
        """Get the value of the submodules flag."""
        return self.submodules
    def getBugs(self):
        """Get the value of the bugs flag."""
        return self.bugs
    def getColors(self):
        """Get the value of the color flag."""
        return self.colors

###############################################################################
# class Repository
###

class Repository:
    """Repository:
    Class representing a Git repository.
    """

    def __init__(self, workTree, gitDir=None, repoFlags=None):
        """Initialize a Repository object."""
        self.workTree = workTree
        if gitDir is None:
            self.gitDir = workTree + '/.git'
        else:
            self.gitDir = gitDir

        if repoFlags is None:
            self.repoFlags = RepositoryFlags()
        else:
            self.repoFlags = repoFlags

        self.repoInfo = RepositoryInfo()
        self.submoduleUTD = False
        self.workingTreeUTD = False
        self.submodules = list()

    def status(self, stats, begin=''):
        """
        PUBLIC. Get status of the repository
        """
        if not self.workingTreeUTD:
            self.populateRepoInfo()

        # When support is added for remote branches, it needs to go here.
        if self.repoFlags.getSubmodules() and not self.submoduleUTD:
            self.populateSubmoduleInfo()

        if not self.repoInfo.hasChanges():
            return (self.repoInfo.hasChanges(), '')

        stats = self.makeSummaryString(stats, begin=begin)
        return (self.repoInfo.hasChanges(), stats)

    def makeSummaryString(self, stats, begin=''):
        """
        INTERNAL. Performs string operations to generate the status string that
        might get printed by the caller. This method treats `stats' like a
        terminal object.
        """
        repoPath = self.workTree.replace(os.environ['HOME'], "~")
        if repoPath[len(repoPath) - 1] == '/':
            repoPath = repoPath[:-1]

        # Prepare status string, maybe with colors.
        repoStatus = self.repoInfo.getStatus()
        if self.repoFlags.getColors():
            repoStatus = TerminalColors.red + repoStatus + TerminalColors.none

        # Get status of bugs
        if self.repoFlags.getBugs():
            if self.repoFlags.getColors():
                repoStatus = (TerminalColors.cyan
                              + self.repoInfo.getBugStatus()
                              + TerminalColors.none + repoStatus)
            else:
                repoStatus = self.repoInfo.getBugStatus() + repoStatus

        # Put together the status string for THIS repository
        stats = (stats + repoStatus + ' ' + repoPath + '\n')

        # Do (ERE) 's#//+#/#g'
        stats = '/'.join(filter(None, stats.split('/'))) # s'#//\+##g'
        # Put together the status string for submodules
        if self.repoFlags.getSubmodules():
            for module in self.submodules:
                submoduleStatus = begin + '\t'
                changes, submoduleStatus = module.status(submoduleStatus,
                                                         begin=begin + '\t')
                if changes:
                    stats = (stats + submoduleStatus.replace(repoPath, ''))
        return stats

    def populateRepoInfo(self):
        """
        INTERNAL. Execute Git commands to populate the fields of this
        RepositoryInfo object.
        """
        self.checkWorkingTree()
        self.checkBugs()

        self.workingTreeUTD = True
        return self.repoInfo.hasChanges()

    def checkWorkingTree(self):
        """
        INTERNAL. Runs git commands to check the status of the working tree and
        populates the RepositoryInfo object as a side effect
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
                self.repoInfo.setChanges(True)
            if (len(line[0]) > 1 and '?' not in line[0]) \
               or (not line[0] and line[1]):
                self.repoInfo.setUnstaged(1)
                self.repoInfo.setChanges(True)
            elif '?' in line[0]:
                self.repoInfo.setUntracked(1)
                self.repoInfo.setChanges(True)

    def checkBugs(self):
        """
        INTERNAL. Checks the status of the Repository's bugs file and set the
        corresponding fields in this RepositoryInfo object.
        """
        if self.repoFlags.getBugs():
            try:
                with open(self.workTree + '/bugs', 'r'):
                    self.repoInfo.setBugs(True)
                    self.repoInfo.setChanges(True)
            except FileNotFoundError:
                pass

    def populateSubmoduleInfo(self):
        """INTERNAL. Execute Git commands to populate self.submodules"""
        entries = self.parseGitmodules(self.workTree + '/.gitmodules')
        for entry in entries:
            # Instantiate the submodule
            submodule = Repository(workTree=(self.workTree + '/'
                                             + entry['path']),
                                   gitDir=(self.gitDir + '/modules/'
                                           + entry['name']),
                                   repoFlags=self.repoFlags)
            if submodule.populateRepoInfo():
                self.repoInfo.setChanges(True)
            if submodule.populateSubmoduleInfo():
                self.repoInfo.setChanges(True)
            self.submodules.append(submodule)

        self.submoduleUTD = True
        return self.repoInfo.hasChanges()

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
