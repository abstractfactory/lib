
import os
import sys
import logging
import subprocess

import lib
import lib.command
import lib.application

# Cross-platform command for clearing shell
clear_cmd = "cls" if os.name == "nt" else "clear"
cls = lambda: subprocess.call(clear_cmd, shell=True)

log = logging.getLogger('lib')
log.setLevel(logging.DEBUG)

log = logging.getLogger('pifou')
if not log.handlers:
    import pifou
    log = pifou.setup_log()

log.setLevel(logging.DEBUG)


def init_shell():
    sys.stdout.write('command> ')


if __name__ == '__main__':
    """Client ('customer')"""
    cls()

    invoker = lib.application.Invoker()

    try:
        while True:
            init_shell()
            input_ = raw_input()

            parts = input_.split()
            try:
                cmd, args = parts[0], parts[1:]
                invoker.execute(cmd, *args)
            except IndexError:
                pass

    except KeyboardInterrupt:
        print "\nGood bye"
