# Remember that project you forgot to finish? #

Sysgit does.

I wrote this as a tool for myself, because I have an *absurd* number of
repositories on my system (something like 80, last time I counted). Keeping
track of all of those repositories becomes a nightmare, especially when there
are so many different states that a git repository can be in, and there's only
one that you want to see:

```
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
```

# How to use it #

It's a fairly simple tool, with a small number of functions. Executing the
script `sysgit.py` with no arguments yields the usage information. Running
`sysgit <subcommand> -h` prints useful information about that subcommand.

The script depends on two environment variables in the shell.

- `SYSGIT_PATH`: Contains a colon separated list of paths to search for git
   repositories
- `SYSGIT_IGNORE`: Colon separated list of strings that, if appearing in the
   path of any git repository found, indicate that repository should be
   ignored.

The output can appear a little cryptic, which is why `sysgit.py list -h`
contains information for deciphering the output:

## Getting the state of your repositories ##

Using the `list` subcommand will print the names and state of any repositories
that have changes. By default, Sysgit will only list repositories that have
changes to the local tree on the checked out branch. The status string appears
to the left of the absolute path of the repository.

If the status string contains an "S", there are changes to the local tree that
have been staged for commit. If the status string contains an "M", the local
tree contains modifications that have not been staged for commit.
If the status string contains a "?", there are untracked files in the
repository.

There are also other options to the `list` command which enable Sysgit to check
for things such as a non-empty stash, discrepancies between remote and
local refs, the existence of a [bugs](https://github.com/AmateurECE/bugs) file,
and the state of submodules, if they exist. See `sysgit.py list -h` for more
information.
