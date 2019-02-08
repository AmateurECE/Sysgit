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
    parser.add_argument("--no-color", help=('Disable colored output'),
                        action="store_true", default=False)
    subparsers = parser.add_subparsers(dest='function',
                                       help='help for subcommand')
    # { list }
    listParser = subparsers.add_parser('list', help=('list the status of the'
                                                     'system\'s repositories'))
    # List arguments
    listParser.add_argument("-s", "--submodules",
                            help=('Also list the status of the repository\'s'
                                  'submodules'),
                            action="store_true", default=False)
    listParser.add_argument("-b", "--bugs",
                            help=('Also list the status of the repository\'s'
                                  'bugs file'),
                            action="store_true", default=False)
    listParser.add_argument("-p", "--show-stash",
                            help=('Show the number of entries in the stash'),
                            action="store_true", default=False)
    listParser.add_argument("-r", "--remotes",
                            help=('Check the refs of remote branches and'
                                  'against the current repository\'s refs'),
                            action="store_true", default=False)

    # Print help if no arguments were given
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()

    # Parse the arguments
    return parser.parse_args()

def repoList(args):
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
        repos = allRepos

    # Construct RepositoryFlags object
    repoFlags = repository.RepositoryFlags(submodules=args['submodules'],
                                           bugs=args['bugs'],
                                           colors=not args['no_color'],
                                           stash=args['show_stash'],
                                           remotes=args['remotes'])

    # Construct repository objects
    repoInstances = list()
    for repo in repos:
        repoInstances.append(repository.Repository(repo, repoFlags=repoFlags))
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
        'list': listHandler
    }
    return funcs[name]

###############################################################################
# HANDLERS
###

def listHandler(args):
    """
    List all of the repos in the path
    """
    # Sanity check
    if args['function'] != 'list':
        raise RuntimeError('The wrong handler was called.')

    repos = repoList(args)
    for repo in repos:
        stats = ''
        changes, stats = repo.status(stats)
        if changes:
            print(stats, end='')
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
    # sys.exit()

    # Two functions:
    # listHandler(verbose)
    handler = getHandler(arguments['function'])
    handler(arguments)

    # Red, Orange, Yellow, Green, Blue, Indigo, Violet
    # TODO: `update' subcommand: `pull` for all (or one) local repositories
    # TODO: `history' subcommand: view commits created in a span of time.
    #   Examples of time spans:
    #       ~1h (the last hour)
    #       ~10d (the last ten days)
    #       (This pattern also works for `w', `m', `y')
    #       (Since Jan 1, 2000)
    #       (Between Jan 1, 1999 and Jan 1, 2000)
    # TODO: -a, --all: Flag to show ALL repository data
    # TODO: -v, --verbose: Verbose output
    #   * Shows status of HEAD for all local branches and remote branches
    #   * Shows 'XX' if a branch does not have a remote counterpart.
    #   * Shows activity messages (e.g. `MESSAGE: updating remote refs...')
    #   * Shows all repositories, regardless of changes
    #   * Shows directories in SYSGIT_PATH that are not under version control
    #   * Shows full path of submodules
    return 0

if __name__ == '__main__':
    main()

##############################################################################
