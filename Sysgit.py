#!/usr/bin/env python3
"""
Sysgit.py: List status of the system's repositories
"""
###############################################################################
# NAME:             Sysgit.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      System-wide Git tools
#                   # TODO: Fix for git submodule edge cases
#                   As it turns out, there is another kind of git submodule,
#                   which has a full tree in its .git/ directory. The url in
#                   the parent's .gitmodules file is a relative path. Sysgit
#                   does not know how to handle these, and crashes in
#                   Repository.execGit with a SystemError.
#
# CREATED:          11/19/2018
#
# LAST EDITED:      12/23/2018
###

###############################################################################
# IMPORTS
###

from argparse import ArgumentParser, RawTextHelpFormatter
import os
import sys

from Logging import Logger
from Repository import Repository, RepositoryFlags

###############################################################################
# CLASSES
###

#pylint: disable=too-many-instance-attributes
class Sysgit:
    """Contains the Sysgit logic"""

    def __init__(self, args, logFile=sys.stderr):
        # Analogous to command line arguments
        self.argAll = args['all']
        self.argBugs = args['bugs']
        self.argFunction = args['function']
        self.argNoColor = args['no_color']
        self.argRemotes = args['remotes']
        self.argShowStash = args['show_stash']
        self.argSubmodules = args['submodules']
        self.argVerbose = args['verbose']

        # File like object to log to
        self.logger = Logger(logFile)

    def log(self, message):
        """Log `message' to this instance's logFile."""
        if self.argVerbose:
            self.logger.log(message)

    def getReposInPath(self):
        """Return a list of repositories found in SYSGIT_PATH env var."""
        self.log('Enumerating repositories in SYSGIT_PATH')
        paths = [os.path.expanduser(path) for path in
                 os.environ['SYSGIT_PATH'].split(':')]
        repoLocations = list()

        # Recursively find all of the repositories in our path
        for path in paths:
            #pylint: disable=unused-variable
            for dirpath, dirnames, filenames in os.walk(path):
                for direntry in dirnames:
                    if '.git' in direntry:
                        repoLocations.append(dirpath)
                        break
        return repoLocations or []

    def rejectIgnoredRepos(self, repoList):
        """
        If SYSGIT_IGNORE is set in the environment, removes these entries from
        the list `repoList'
        """
        # Try removing all paths in SYSGIT_IGNORE
        try:
            ignoredRepos = [os.path.expanduser(path) for path in
                            os.environ['SYSGIT_IGNORE'].split(':')]
            self.log('Ignoring repos in SYSGIT_IGNORE')
            validRepoList = list()
            for repo in repoList:
                for ignoredRepo in ignoredRepos:
                    if ignoredRepo not in repo:
                        validRepoList.append(repo)
            repoList = validRepoList
        except KeyError:
            # If SYSGIT_IGNORE doesn't exit, we should carry on normally.
            pass
        return repoList

    def buildRepoList(self):
        """
        Get a list of Repository objects corresponding to top-level git
        repositories in the path.
        """
        repoList = self.rejectIgnoredRepos(self.getReposInPath())
        self.log('Discovered {} repositories'.format(len(repoList)))

        # Construct RepositoryFlags object
        repoFlags = RepositoryFlags(submodules=self.argSubmodules,
                                    bugs=self.argBugs,
                                    colors=not self.argNoColor,
                                    stash=self.argShowStash,
                                    remotes=self.argRemotes,
                                    verbose=self.argVerbose)

        # Construct repository objects
        repoInstances = list()
        for repo in repoList:
            repoInstances.append(Repository(repo, repoFlags=repoFlags))
        return repoInstances

    def execute(self):
        """Executes the function of this invocation."""
        # The dict of function handlers.
        funcs = {
            'list': self.listHandler
        }
        handler = funcs[self.argFunction]
        self.log('Executing {}'.format(self.argFunction))
        if not handler():
            self.log('Exiting normally')
        else:
            self.log('Exiting with errors')

    ###########################################################################
    # HANDLERS
    ###

    def listHandler(self):
        """
        List all of the repos in the path
        """
        # Sanity check
        if self.argFunction != 'list':
            raise RuntimeError('The wrong handler was called.')

        if self.argAll:
            self.argSubmodules = True
            self.argBugs = True
            self.argShowStash = True
            self.argRemotes = True

        repos = self.buildRepoList()
        for repo in repos:
            stats = ''
            changes, stats = repo.status(stats)
            if changes or self.argVerbose:
                print(stats, end='')
        return 0

###############################################################################
# FUNCTIONS
###

def parseArgs():
    """
    Parse the command line arguments
    """
    # Parser for all cases but one.
    parser = ArgumentParser()
    parser.add_argument('--no-color', help=('disable colored output'),
                        action='store_true', default=False)
    parser.add_argument('-v', '--verbose',
                        help=('Print messages to stderr during execution (for '
                              'debugging); show all repositories, regardless '
                              'of changes; show directories in SYSGIT_PATH '
                              'that are not under version control'),
                        action='store_true', default=False)
    subparsers = parser.add_subparsers(dest='function',
                                       help='help for subcommand')

    # { list }
    listParser = subparsers.add_parser('list', help=('list the status of the'
                                                     'system\'s repositories'),
                                       formatter_class=RawTextHelpFormatter)
    # List arguments
    listParser.add_argument('-s', '--submodules',
                            help=('list the status of the repository\'s '
                                  'submodules, if they\ncontain changes.'),
                            action='store_true', default=False)
    listParser.add_argument('-b', '--bugs',
                            help=('show "B" in the output if the repository '
                                  'contains a file\nnamed "bugs" in the top '
                                  'level directory (blue).'),
                            action='store_true', default=False)

    listParser.add_argument('-p', '--show-stash',
                            help=('show the number of entries in the '
                                  'repository\'s stash\n(yellow)'),
                            action='store_true', default=False)
    listParser.add_argument('-r', '--remotes',
                            help=("check the refs of remote branches against "
                                  "the local refs:\n"
                                  "  * 'uu': local is up to date w/ remote\n"
                                  "  * 'lr': local is behind remote\n"
                                  "  * 'rl': local is ahead of remote\n"
                                  "  * '<>': local and remote have diverged\n"
                                  "  * '  ': local has no remote branch\n"
                                  "  * '00': local has no commits yet"),
                            action='store_true', default=False)
    listParser.add_argument('-a', '--all', help=('Same as -bspr'),
                            action='store_true', default=False)

    # Print help if no arguments were given
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()

    # Parse the arguments
    return parser.parse_args()

###############################################################################
# MAIN
###

def main():
    """
    List status of the system's repositories
    """
    # Parse arguments
    arguments = vars(parseArgs())

    # Execute the function
    sysgit = Sysgit(arguments)
    sysgit.execute()

    # TODO: -v,--verbose: More information than you ever wanted to know
    #   [x] Shows activity messages (e.g. `MESSAGE: updating remote refs...')
    #   [x] Shows all repositories, regardless of changes
    #   [ ] Shows directories in SYSGIT_PATH that are not under version control

    # TODO: Remove colors.py as submodule, replace with colorama
    #   * And remove --no-color flag, because colorama does nothing on systems
    #     that don't support color.

    # TODO: `update' subcommand: Do all the slow networking operations
    #   * Issues `git remote update' command
    #   * Issues `b update' command
    #   * Issues `git pull && git submodule update --init --recursive'?

    # TODO: `history' subcommand: view commits created in a span of time
    #   Examples of time spans:
    #       ~1h (the last hour)
    #       ~10d (the last ten days)
    #       (This pattern also works for `w', `m', `y')
    #       (Since Jan 1, 2000)
    #       (Between Jan 1, 1999 and Jan 1, 2000)

    # TODO: `info' subcommand: Show extra info about repository:
    #   * Shows status of HEAD for all local branches and remote branches
    #   * Shows 'XX' if a branch does not have a remote counterpart.
    #   * Shows full path of submodules
    return 0

if __name__ == '__main__':
    main()

##############################################################################
