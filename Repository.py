#!/usr/bin/env python3
"""
Implements the Repository object interface
"""
###############################################################################
# NAME:             Repository.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      A repository object.
#
# CREATED:          11/19/2018
#
# LAST EDITED:      03/11/2018
###

###############################################################################
# IMPORTS
###

import subprocess
import os

from RepositoryInfo import RepositoryInfo, BranchStatus

###############################################################################
# class RepositoryFlags
###

class RepositoryFlags:
    """
    Container for data that dictates the format of the status string. This
    class is essentially a Builder class for Repository objects.
    """

    #pylint: disable=too-many-arguments
    def __init__(self, submodules=False, bugs=False, colors=True, stash=False,
                 remotes=False, verbose=False):
        """Initialize a RepositoryFlags object."""
        self.submodules = submodules
        self.bugs = bugs
        self.colors = colors
        self.stash = stash
        self.remotes = remotes
        self.verbose = verbose

    def getSubmodules(self):
        """Get the value of the submodules flag."""
        return self.submodules
    def getBugs(self):
        """Get the value of the bugs flag."""
        return self.bugs
    def getColors(self):
        """Get the value of the color flag."""
        return self.colors
    def getStash(self):
        """Get the value of the stash flag."""
        return self.stash
    def getRemotes(self):
        """Get the value of the remotes flag."""
        return self.remotes
    def getVerbose(self):
        """Get the value of the verbose flag."""
        return self.verbose

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

        self.repoInfo = RepositoryInfo(self.repoFlags)
        self.submoduleUTD = False
        self.workingTreeUTD = False
        self.submodules = list()

    def status(self, stats, begin=''):
        """
        PUBLIC. Get status of the repository
        """
        if not self.workingTreeUTD:
            self.populateRepoInfo()

        if self.repoFlags.getSubmodules() and not self.submoduleUTD:
            self.populateSubmoduleInfo()

        stats = self.makeSummaryString(stats, begin=begin)
        return (self.repoInfo.hasChanges(), stats)

    def makeSummaryString(self, stats, begin=''):
        """
        INTERNAL. Performs string operations to generate the status string that
        might get printed by the caller. This method treats `stats' like a
        terminal object.
        """
        # Replace $HOME with '~' for printing
        repoPath = self.workTree.replace(os.environ['HOME'], "~")
        # Remove a trailing slash, if it exists
        if repoPath[len(repoPath) - 1] == '/':
            repoPath = repoPath[:-1]

        # Do (ERE) 's#//+#/#g'
        stats = '/'.join(filter(None, stats.split('/'))) # s'#//\+##g'
        # Prepare status string
        repoStatus = stats + str(self.repoInfo) + ' ' + repoPath + '\n'

        # Put together the status string for submodules
        if self.repoFlags.getSubmodules():
            for module in self.submodules:
                submoduleStatus = begin + '\t'
                changes, submoduleStatus = module.status(submoduleStatus,
                                                         begin=begin + '\t')
                # Print all submodules if -v is specified
                if changes or self.repoFlags.getVerbose():
                    # Print the whole path of the submodule if -v is specified
                    if self.repoFlags.getVerbose():
                        repoStatus = (repoStatus + submoduleStatus)
                    else:
                        repoStatus = (repoStatus +
                                      submoduleStatus.replace(repoPath, ''))
        return repoStatus

    def populateRepoInfo(self):
        """
        INTERNAL. Execute Git commands to populate the fields of this
        RepositoryInfo object.
        """
        self.checkWorkingTree()
        self.checkBugs()
        self.checkStash()
        self.checkRemotes()

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
        pipe = self.execGit(cmd.replace('xGD', self.gitDir)
                            .replace('xWT', self.workTree))

        # Parse the output and populate the fields.
        for line in pipe.stdout.readlines():
            line = line.decode('utf-8').split(' ')
            if line[0] and '?' not in line[0]:
                self.repoInfo.getTreeInfo().setStaged(1)
                self.repoInfo.setChanges(True)
            if (len(line[0]) > 1 and '?' not in line[0]) \
               or (not line[0] and line[1]):
                self.repoInfo.getTreeInfo().setUnstaged(1)
                self.repoInfo.setChanges(True)
            elif '?' in line[0]:
                self.repoInfo.getTreeInfo().setUntracked(1)
                self.repoInfo.setChanges(True)

    def checkBugs(self):
        """
        INTERNAL. Checks the status of the Repository's bugs file and set the
        corresponding fields in this RepositoryInfo object.
        """
        if self.repoFlags.getBugs():
            try:
                with open(self.workTree + '/bugs', 'r'):
                    self.repoInfo.getBugInfo().setBugs(True)
                    self.repoInfo.setChanges(True)
            except FileNotFoundError:
                pass

    def checkStash(self):
        """
        INTERNAL. Check the status of the repository's stash, and the number of
        entries therein.
        """
        if self.repoFlags.getStash():
            try:
                with open(self.gitDir + '/refs/stash', 'r') as stashFile:
                    (self.repoInfo.getStashInfo()
                     .setStashEntries(len(stashFile.readlines())))
                    self.repoInfo.setChanges(True)
            except FileNotFoundError:
                pass

    def checkRemotes(self):
        """
        INTERNAL. Compare refs of the local branches against the remote refs
        """
        # TODO: Refactor Repository.checkRemotes()
        if not self.repoFlags.getRemotes():
            return

        # Update remote refs
        self.execGit('git remote update')

        # Get the name of the refs
        localRefs = os.listdir(self.gitDir + '/refs/heads')
        remoteRefs = list()
        try:
            for remote in os.listdir(self.gitDir + '/refs/remotes'):
                for ref in os.listdir(self.gitDir + '/refs/remotes/' + remote):
                    remoteRefs.append(remote + '/' + ref)
        except FileNotFoundError:
            for local in localRefs:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.NO_REMOTE))

        # There's likely to be fewer locals than remotes (in large projects)
        for local in localRefs:
            remote = None
            for ref in remoteRefs:
                pieces = ref.split('/')
                if local == pieces[-1]:
                    # Remote refs in git are labelled remote/branch
                    remote = '/'.join(pieces[-2:])
                    break

            if remote is None:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.NO_REMOTE))
                continue

            revParseCmd = 'git --git-dir=xGD --work-tree=xWT rev-parse '
            mergeBaseCmd = 'git --git-dir=xGD --work-tree=xWT merge-base '
            localHash = (self.execGit(revParseCmd
                                      .replace('xGD', self.gitDir)
                                      .replace('xWT', self.workTree)
                                      + str(local))
                         .stdout.readlines()[0])
            remoteHash = (self.execGit(revParseCmd
                                       .replace('xGD', self.gitDir)
                                       .replace('xWT', self.workTree)
                                       + str(remote))
                          .stdout.readlines()[0])
            baseHash = (self.execGit(mergeBaseCmd
                                     .replace('xGD', self.gitDir)
                                     .replace('xWT', self.workTree)
                                     + str(local) + ' ' + str(remote))
                        .stdout.readlines()[0])

            # Compare the hashes and set the status of the branch.
            if localHash == remoteHash:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.UP_TO_DATE))
            elif localHash == baseHash:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.BEHIND))
                self.repoInfo.setChanges(True)
            elif remoteHash == baseHash:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.AHEAD))
                self.repoInfo.setChanges(True)
            else:
                (self.repoInfo.getBranchInfo()
                 .setBranchStatus(local, BranchStatus.DIVERGED))
                self.repoInfo.setChanges(True)

    def populateSubmoduleInfo(self):
        """INTERNAL. Execute Git commands to populate self.submodules"""
        entries = self.parseModuleFile(self.workTree + '/.gitmodules')
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
    def parseGitmodules(lines):
        """
        INTERNAL. Assumes moduleFile is a list of lines from a .gitmodules file
        and parses it accordingly.
        """
        # TODO: Move git specific logic to separate module
        #   * And use dependency injection to populate Repository
        #   * Alternatively, use inheritance: class GitRepository(Repository)
        try:
            while True:
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


    @staticmethod
    def parseModuleFile(path):
        """INTERNAL. Parse the .gitmodules file @ path into a list of dicts."""
        entries = list()
        try:
            with open(path, 'r') as gitmodules:
                # Parse the .gitmodules file.
                lines = gitmodules.readlines()
                entries = parseGitmodules(lines)
        except FileNotFoundError:
            pass
        return entries

    @staticmethod
    def execGit(cmd):
        """INTERNAL. Spawns a subprocess to execute a git command"""
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        pipe.wait()
        if pipe.returncode != 0:
            raise SystemError(('git did not exit successfully. Command:\n'
                               '{}').format(cmd))
        return pipe

##############################################################################
