
import cmd
import os
import sys
import threading
import time

import copiscore


class copisconsole(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)

        self.c = copiscore.COPISCore()
