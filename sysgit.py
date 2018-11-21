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
# LAST EDITED:      11/21/2018
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
    repos = list()

    # TODO: (1) Recursively find repositories in directory
    # TODO: (2) Then remove duplicates
    for path in paths:
        repos.append(repository.Repository(path))
    if len(repos) == 0:
        raise EnvironmentError('SYSGIT_PATH is undefined')
    return repos

def listHandler(verbose=False):
    """
    List all of the repos in the path
    """
    repos = repoList()
    for repo in repos:
        repo.status(verbose)
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
