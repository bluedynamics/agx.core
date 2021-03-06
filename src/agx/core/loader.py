import sys
import traceback
from pkg_resources import iter_entry_points


def get_entry_points(ns=None):
    entry_points = []
    for ep in iter_entry_points('agx.generator'):
        if ns is not None and ep.name != ns:
            continue
        entry_points.append(ep)
    return entry_points


for ep in get_entry_points('register'):
    try:
        ep.load()()
    except:
        print >> sys.stderr,'Error importing generator package ', ep.module_name
        print >> sys.stderr,'===================================='
        traceback.print_exc(None)
        
