#!/usr/bin/env python3
"""Contains the state of the repository"""
###############################################################################
# NAME:             RepositoryInfo.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# CREATED:          03/11/2019
#
# LAST EDITED:      03/11/2019
###

from enum import Enum
from abc import ABC, abstractmethod

import colors as TerminalColors

###############################################################################
# Auxiliary Classes
###

class iInfo(ABC):
    """Info interface stub. Currently unused."""
    # TODO: Integrate iInfo
    def __init__(self, colors):
        self.colors = colors
        super().__init__()

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def hasChanges(self):
        """
        Returns True if this Info instance contains information about an
        unclean repository.
        """

class BranchStatus(Enum):
    """Enum used to specify status of branch ref"""
    UP_TO_DATE = 0
    BEHIND = 1
    AHEAD = 2
    DIVERGED = 3
    NO_REMOTE = 4

class BranchInfo:
    """Contains the state of the repository's branches."""
    def __init__(self, colors=True):
        self.branches = dict()
        self.colors = colors
        self.branchStatusStrings = {
            BranchStatus.UP_TO_DATE: 'uu',
            BranchStatus.BEHIND: 'lr',
            BranchStatus.AHEAD: 'rl',
            BranchStatus.DIVERGED: '<>',
            BranchStatus.NO_REMOTE: '  '
        }

    def __str__(self):
        """Return a string object representing this BranchInfo instance."""
        try:
            # TODO: Consider another color besides fuscia
            string = self.branchStatusStrings[self.branches['master']]
            if self.colors:
                string = (TerminalColors.fuscia
                          + string
                          + TerminalColors.none)
            return string
        except KeyError:
            # This occurs, e.g. if a repo has zero commits
            string = '00'
            if self.colors:
                string = TerminalColors.fuscia + string + TerminalColors.none
            return string

    def setBranchStatus(self, branch, status):
        """Set the status of the branch indicated by the string `branch'"""
        if not isinstance(status, BranchStatus):
            raise ValueError('{} is not a valid branch status'.format(status))
        self.branches[branch] = status

    def getBranchStatus(self, branch):
        """Return a string representing the status of the branch."""
        if not self.branches:
            return '00' # Means there are no commits yet
        return self.branchStatusStrings[self.branches[branch]]

class TreeInfo:
    """Contains the state of the working tree."""
    def __init__(self, colors=True):
        self.workingTreeInfo = {'S': 0, 'M': 0, '?': 0}
        self.colors = colors

    def __str__(self):
        """Get a string representing the repository's working tree status."""
        stats = ''
        for key in self.workingTreeInfo:
            if self.workingTreeInfo[key]:
                stats += key
            else:
                stats += ' '

        if self.colors:
            stats = TerminalColors.red + stats + TerminalColors.none
        return stats

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

class StashInfo:
    """Encapsulates data about the stash."""
    def __init__(self, colors=True):
        self.stashEntries = 0
        self.colors = colors

    def __str__(self):
        """Return a string representing this instance of StashInfo."""
        string = ' '
        if self.stashEntries > 0:
            string = str(self.stashEntries)
        if self.colors:
            string = TerminalColors.yellow + string + TerminalColors.none
        return string

    def setStashEntries(self, stashEntries):
        """Set the number of stash entries"""
        self.stashEntries = stashEntries
    def getStashEntries(self):
        """Return the number of stash entries"""
        return self.stashEntries

class BugInfo:
    """Encapsulates data about the state of the bugs file in the repository."""
    def __init__(self, colors=True):
        self.bugs = False
        self.colors = colors

    def __str__(self):
        """Get a string representing the status of the bugs file."""
        string = ' '
        if self.bugs:
            string = 'B'
        if self.colors:
            string = TerminalColors.cyan + string + TerminalColors.none
        return string

    def setBugs(self, bugs):
        """Set state of repository's bugs file."""
        self.bugs = bugs
    def getBugs(self):
        """Return state of repository's bugs file."""
        return self.bugs

###############################################################################
# class RepositoryInfo
###

class RepositoryInfo:
    """RepositoryInfo
    Contains the state of the repository object.
    """
    def __init__(self, repoFlags):
        """Initialize a new RepositoryInfo object."""
        self.changes = False
        # Set up list of info instances using information in repoFlags
        self.info = dict()
        if repoFlags.getRemotes():
            self.info['BranchInfo'] = BranchInfo(repoFlags.getColors())

        if repoFlags.getBugs():
            self.info['BugInfo'] = BugInfo(repoFlags.getColors())

        if repoFlags.getStash():
            self.info['StashInfo'] = StashInfo(repoFlags.getColors())

        # Always do working tree info.
        self.info['TreeInfo'] = TreeInfo(repoFlags.getColors())

    def __str__(self):
        """Return a string representing this instance of RepositoryInfo."""
        # Iterate in this order: BranchInfo, BugInfo, StashInfo, TreeInfo
        # Since this order is alphabetic, we don't need to worry much about it.
        statusString = ''
        for key in self.info:
            statusString = statusString + str(self.info[key])
        return statusString

    def setChanges(self, hasChanges):
        """Set status of repository's hasChanges flag."""
        self.changes = hasChanges
    def hasChanges(self):
        """Return status of repository's hasChanges flag."""
        return self.changes

    def infoInstance(self, key):
        """
        Return a pointer to the instance of Info object in the dict w/ key
        """
        try:
            return self.info[key]
        except KeyError:
            return None

    def getBranchInfo(self):
        """Get a pointer to this BranchInfo instance"""
        return self.infoInstance('BranchInfo')
    def getBugInfo(self):
        """Get a pointer to this BugInfo instance"""
        return self.infoInstance('BugInfo')
    def getStashInfo(self):
        """Get a pointer to this StashInfo instance"""
        return self.infoInstance('StashInfo')
    def getTreeInfo(self):
        """Get a pointer to this TreeInfo instance"""
        return self.infoInstance('TreeInfo')

##############################################################################
