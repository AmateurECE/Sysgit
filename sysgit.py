#!/usr/bin/env python3
###############################################################################
# NAME:             sysgit.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      System-wide Git tools
#
# CREATED:          11/19/2018
#
# LAST EDITED:      12/05/2018
###

###############################################################################
# IMPORTS
###

import sys
import os
import repository

###############################################################################
# FUNCTIONS
###

def repoList():
    """
    Get the list of repos in the path
    """
    paths = os.environ['SYSGIT_PATH'].split(':')
    repoLocations = list()

    # Recursively find all of the repositories in our path
    for path in paths:
        stack = enumerateRepositories(repoLocations, os.path.expanduser(path))
        repoLocations.extend(stack)

    # Remove duplicates and construct Repository objects
    repos = list()
    for repo in list(dict.fromkeys(repoLocations)):
        repos.append(repository.Repository(repo))
    return repos

def enumerateRepositories(stack, rootPath):
    nextLevel = list()
    for entry in os.listdir(rootPath):
        path = os.path.join(rootPath, entry)
        if os.path.isdir(path):
            if '.git' in entry:
                stack.append(rootPath)
                return stack # No .git dirs inside of .git dirs
            nextLevel.append(path)
    for path in nextLevel:
        stack = enumerateRepositories(stack, path)
    return stack

def listHandler(verbose=False):
    """
    List all of the repos in the path
    """
    repos = repoList()
    for repo in repos:
        changes, stats = repo.status(verbose)
        if changes:
            print(stats)
    return 0

def infoHandler(repoName, verbose=False):
    """
    Get info on the repository with name `repoName`
    """
    repos = repoList()
    for repo in repos:
        name = repo.split('/')
        if name[:-1] is repoName:
            repo.info(verbose)
    return 0

###############################################################################
# MAIN
###

def main():
    verbose = False

    # First, if we have specified no arguments, just execute list
    if len(sys.argv) <= 1:
        listHandler(verbose=False)

    # We're going to eventually replace this logic with something more
    # maintainable.
    for arg in sys.argv[1:]:
        if arg is '-v':
            verbose = True

    # TODO: Dictate output format by invocation switches
    # TODO: Output if `bugs` are present
    # TODO: Output if HEAD and remote refs differ
    # TODO: Output if there is no remote
    # TODO: Add SYSGIT_IGNORE env var.

    # Check for list
    for arg in sys.argv[1:]:
        if arg is 'list':
            return listHandler(verbose)

    # Check for info
    for i in range(1, len(sys.argv) - 1):
        if sys.argv[i] is 'info':
            return infoHandler(sys.argv[i+1], verbose)
    return 1

if __name__ == '__main__':
    main()

##############################################################################
