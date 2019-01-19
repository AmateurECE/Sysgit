#!/usr/bin/env python3
"""
List status of the system's repositories
"""
###############################################################################
# NAME:             sysgit.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      System-wide Git tools
#
# CREATED:          11/19/2018
#
# LAST EDITED:      12/23/2018
###

###############################################################################
# IMPORTS
###

import argparse
import os
import sys
import repository

###############################################################################
# FUNCTIONS
###

def parseArgs():
    """
    Parse the command line arguments
    """
    # Parser for all cases but one.
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='function',
                                       help='help for subcommand')
    # { list }
    listParser = subparsers.add_parser('list', help=('list the status of the'
                                                     'system\'s repositories'))
    # [ -v, --verbose ]
    listParser.add_argument('-v', '--verbose', help='verbose output',
                            action='store_true', default=False)
    # { info }
    infoParser = subparsers.add_parser('info',
                                       help=('get more info about the status'
                                             'of a particular repository'))
    # [ -v, --verbose ]
    infoParser.add_argument('-v', '--verbose', help='verbose output',
                            action='store_true', default=False)
    # { <repository> }
    infoParser.add_argument('repository', help='The path of the repository')

    # Print help if no arguments were given
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()

    # Parse the arguments
    return parser.parse_args()

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

    # With the current recursive implementation, duplicates of some
    # repositories may occur in repoLocations. We can save a few cycles by
    # eliminating them here, instead of in the loop.
    allRepos = list(dict.fromkeys(repoLocations))
    repos = list()

    # Try removing all paths in SYSGIT_IGNORE
    try:
        ignoredRepos = os.environ['SYSGIT_IGNORE'].split(':')
        for repo in allRepos:
            for ignoredRepo in ignoredRepos:
                if os.path.expanduser(ignoredRepo) not in repo:
                    repos.append(repo)
    except KeyError:
        # If SYSGIT_IGNORE doesn't exit, we should carry on normally.
        pass

    # Construct repository objects
    repoInstances = list()
    for repo in repos:
        repoInstances.append(repository.Repository(repo))
    return repoInstances

def enumerateRepositories(stack, rootPath):
    """
    Find all git repositories in all subpaths of all paths in SYSGIT_PATH.
    """
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

def getHandler(name):
    """
    Return a function to handle the requested service
    """
    # The dict of function handlers.
    funcs = {
        'list': listHandler,
        'info': infoHandler
    }
    return funcs[name]

###############################################################################
# HANDLERS
###

def listHandler(args):
    """
    List all of the repos in the path
    """
    repos = repoList()
    for repo in repos:
        changes, stats = repo.status(args['verbose'])
        if changes:
            print(stats)
    return 0

def infoHandler(args):
    """
    Get info on the repository with name `repoName`
    """
    repo.info(args['verbose'])
    return 0

###############################################################################
# MAIN
###

def main():
    """
    List status of the system's repositories
    """
    # Parse arguments
    arguments = vars(parseArgs())
    # For debugging:
    # for key in arguments:
    #     print('{}: {}'.format(key, arguments[key]))

    # Two functions:
    # listHandler(verbose)
    # infoHandler(repository, verbose)
    handler = getHandler(arguments['function'])
    handler(arguments)

    # TODO: -s, --submodules: also get status of submodules
    # TODO: -b, --bugs: Output if `bugs` is present
    # TODO: -r, --remote: Output status of remote
    #   Output based on whether local:
    #       - is up to date with remote
    #       - is behind remote
    #       - is ahead of remote
    #       - has diverged from remote
    #       - has no remote
    # TODO: -b, --branches: Output for all local branches
    # TODO: Update subcommand: `git push` for all (or one) local repository
    return len(arguments)

if __name__ == '__main__':
    main()

##############################################################################
