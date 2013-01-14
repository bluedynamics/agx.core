import sys


def postmortem(type, value, tb):
    # from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65287
    if hasattr(sys, 'ps1') or not (
        sys.stderr.isatty() and sys.stdin.isatty()):
        sys.__excepthook__(type, value, tb)
    else:
        import traceback, pdb
        traceback.print_exception(type, value, tb)
        print
        pdb.pm()


def opt_callback(option, opt, value, parser):
    sys.excepthook = postmortem
