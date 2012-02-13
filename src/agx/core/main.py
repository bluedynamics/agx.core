# XXX: this main should be moved from agx.core to somewhere.

from agx.core import loginitializer
loginitializer.initLog('agx.core.log')
loginitializer.loghandler = loginitializer.addConsoleLogging()
# End of the stuff that needs to be handled first.

import os
import sys
import re
import shutil
import agx.core
from time import time
from pkg_resources import resource_string
from optparse import OptionParser
from zope.component import getUtility
from zope.configuration.xmlconfig import XMLConfig
from agx.core.interfaces import IConfLoader
from agx.core import postmortem
import logging

log = logging.getLogger('main')

ARCHGENXML_VERSION_LINE = "AGX %s - (c) BlueDynamics Alliance, " +\
                          "http://bluedynamics.com, GPL 2"


def version():
    ver = resource_string(__name__, os.path.join('version.txt')).strip()
    return str(ver)


parser = OptionParser("Usage: agx UMLFILE options")

def parse_options():
    parser.add_option("-o", "--output-directory", dest="outdir", default='.',
                      help="Write generated code to TARGET", metavar="/target/path")
    parser.add_option("-p", "--profiles", dest="profiles", default='',
                      help="Comma seperated Paths to profile file(s)",
                      metavar="/path/to/profile1.uml;/path/to/profile2.uml")
    parser.add_option("-e", "--export-profiles", dest="export", default='',
                      help="Comma seperated profile names to export for model",
                      metavar='profilename1;profilename2')
    parser.add_option("-l", "--listprofiles",
                      action="store_false", dest="listprofiles",
                      default='unset', help="List of available profiles")
    parser.add_option("-i", "--info",
                      action="store_false", dest="info",
                      default='unset', help="AGX Version and flavour info.")
    parser.add_option("-d", "--debug",
                      action="callback", callback=loginitializer.opt_callback,
                      default=False,
                      help="Additional output of debug information.")
    parser.add_option("-m", "--postmortem",
                      action="callback",  callback=postmortem.opt_callback,
                      default=False, help="Enable postmortem debugger.")
    return parser.parse_args()


def avaliable_profiles():
    confloader = getUtility(IConfLoader)
    for profile in confloader.profiles:
        print '%s %s' % (profile[0], profile[1])


def agx_export(modelpath, profilenames):
    if not os.path.exists(modelpath):
        log.error("Model path does not exist.")
        sys.exit(2)
    confloader = getUtility(IConfLoader)
    profiles = list()
    for profile in confloader.profiles:
        if profile[0] in profilenames:
            profiles.append(profile)
            continue
    if not profiles:
        log.error("One or more profiles not provided")
        sys.exit(2)
    target = modelpath[:modelpath.rfind(os.path.sep)]
    log.info("Export to target: '%s'" % target)
    for profile in profiles:
        log.info("Export '%s' " % profile[0])
        shutil.copy(profile[1], target)


def agx_info():
    version = open(os.path.join(os.path.dirname(agx.core.__file__),
                   'version.txt')).read()
    confloader = getUtility(IConfLoader)
    flavour = confloader.flavour
    print 'AGX %s %s' % (version, flavour)


def run():
    starttime = time()
    options, args = parse_options()
    if options.listprofiles != 'unset':
        avaliable_profiles()
        return
    if options.info != 'unset':
        agx_info()
        return
    if len(args) != 1:
        log.critical("No control flags given.")
        parser.print_help()
        sys.exit(2)
    if options.export != '':
        agx_export(args[0], options.export.split(';'))
        return
    log.info(ARCHGENXML_VERSION_LINE, version())
    XMLConfig('configure.zcml', agx.core)()
    modelpath = args[0]
    modelprofiles = options.profiles.strip()
    if modelprofiles:
        modelprofiles = re.split('[;,]',modelprofiles)
    else:
        modelprofiles = []
    modelpaths = [modelpath] + modelprofiles
    controller = agx.core.Controller()
    controller(modelpaths, options.outdir)
    log.info('Generator run took %1.2f sec.' % (time() - starttime))
