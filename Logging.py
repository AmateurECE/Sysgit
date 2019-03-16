#!/usr/bin/env python3
"""Implements logic related to logging."""
###############################################################################
# NAME:             Logging.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Implements logging logic.
#
# CREATED:          03/10/2019
#
# LAST EDITED:      03/10/2019
###

import colors as TerminalColors

###############################################################################
# CLASSES
###

class Logger:
    """Encapsulates message logging logic"""

    def __init__(self, logFile, color=True):
        self.logFile = logFile
        self.color = color

    def getLogFile(self):
        """Return a file-like object representing the logfile."""
        return self.logFile

    def log(self, message):
        """Print a message to the log."""
        if self.color:
            message = (TerminalColors.yellow + 'MSG' + TerminalColors.none
                       + ': ' + message)
        else:
            message = 'MSG: ' + message
        print(message, file=self.logFile, flush=True)

##############################################################################
