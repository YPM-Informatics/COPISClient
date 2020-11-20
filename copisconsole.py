"""
Console command processor. Headless.

TODO: The entire thing is a todo
"""


import cmd

import copiscore


class COPISConsole(cmd.Cmd):
    """COPISConsole."""

    def __init__(self):
        cmd.Cmd.__init__(self)

        self.c = copiscore.COPISCore()
