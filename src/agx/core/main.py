from agx.core import loginitializer

loginitializer.initLog('agx.core.log')
loginitializer.loghandler = loginitializer.addConsoleLogging()
# End of the stuff that needs to be handled first.

import os
import sys
import re
import shutil
import ConfigParser
from StringIO import StringIO
import agx.core
from time import (
    time,
    strftime,
    gmtime,
)
from pkg_resources import resource_string
from optparse import OptionParser
from zope.component import getUtility
from zope.configuration.xmlconfig import XMLConfig
from agx.core.interfaces import IConfLoader
from agx.core import postmortem
import logging


log = logging.getLogger('main')


ARCHGENXML_VERSION_LINE = "AGX %s - (c) BlueDynamics Alliance, " + \
                          "http://bluedynamics.com, GPL 2"


def version():
    ver = resource_string(__name__, os.path.join('version.txt')).strip()
    return str(ver)


parser = OptionParser("Usage: agx UMLFILE options")


def parse_options():
    parser.add_option("-o", "--output-directory", dest="outdir",
                      help="Write generated code to TARGET",
                      metavar="/target/path")
    parser.add_option("-p", "--profiles", dest="profiles", default='',
                      help="Comma separated Paths to profile file(s)",
                      metavar="/path/to/profile1.uml;/path/to/profile2.uml")
    parser.add_option("-e", "--export-profiles", dest="export", default='',
                      help="Comma separated profile names to export for model",
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
                      action="callback", callback=postmortem.opt_callback,
                      default=False, help="Enable postmortem debugger.")
    parser.add_option("-t", "--listtemplates",
                      action="store_false", dest="listtemplates",
                      default='unset', help="list available model templates")
    parser.add_option("-c", "--create", dest="create_model", 
                      help="Create a model from a model template by name. (see '-t' option)",
                      metavar="template_name")
    parser.add_option("-s", "--short", default="unset",
                      action='store_false', dest="short_messages",
                      help="option for short machine readable messages")
    return parser.parse_args()


def avaliable_profiles():
    confloader = getUtility(IConfLoader)
    for profile in confloader.profiles:
        print '%s %s' % (profile[0], profile[1])


def avaliable_templates(short=False):
    confloader = getUtility(IConfLoader)
    for template in confloader.templates:
        if short:
            print '%s\t%s\t%s' % \
                (template[0], template[1], template[2].replace('\n', '<br/>'))
        else:
            print '%s: %s\n\t%s' % (template[0], template[1], template[2].replace('\n','\n\t'))
            print


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
    profilepath = os.path.join(target, 'uml_profiles')
    if not os.path.exists(profilepath):
        os.mkdir(profilepath)
    if not os.path.isdir(profilepath):
        log.error("%s is not a directory" % profilepath)
        sys.exit(2)
    log.info("Export to target: '%s'" % profilepath)
    for profile in profiles:
        log.info("Export '%s' " % profile[0])
        shutil.copy(profile[1], profilepath)


def agx_info():
    version = open(os.path.join(os.path.dirname(agx.core.__file__),
                   'version.txt')).read()
    confloader = getUtility(IConfLoader)
    flavour = confloader.flavour
    info = 'AGX %s %s\n' % (version, flavour)
    generators = confloader.generators
    info += 'Installed generators:\n'
    for name, version in generators:
        info += '    %s (%s)\n' % (name, version)
    print info


def prepare_model_path(modelpath):
    """Unifies the containing dir of model, the .agx  and the .uml filename
    if no .agx is present, None is returned.
    """
    agx = None
    uml = None
    localdir = os.path.abspath(os.path.dirname(modelpath))
    modelfile = os.path.split(modelpath)[1]
    if modelfile.endswith('.agx'):
        agx = modelfile
        uml = modelfile[:-4]
    elif modelfile.endswith('.uml'):
        uml = modelfile
        if os.path.exists(os.path.join(localdir, uml) + '.agx'):
            agx = uml + '.agx'
    else: # no file suffix given
        uml = modelfile + '.uml'
        if os.path.exists(os.path.join(localdir, uml) + '.agx'):
            agx = uml + '.agx'
    return localdir, uml, agx


def read_config(localdir, agx):
    """Parses the .agx file and extracts the profiles list and target dir.
    """
    profiles = []
    target = None
    buf = '[default]\n' + open(os.path.join(localdir, agx)).read()
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(StringIO(buf))
    if cp.has_option('default', 'profiles'):
        profiles = re.split('[;,]', cp.get('default', 'profiles'))
    if cp.has_option('default', 'target'):
        target = cp.get('default', 'target')
    return [p.strip() for p in profiles], target


def unify_profile_paths(localdir, profiles):
    """make absolute paths from the profiles.
    """
    res = []
    # get the profile paths from the config
    conf = getUtility(IConfLoader)
    profdict = {}
    for name, path in conf.profiles:
        profdict[name] = path
    # unify the profile paths into absolute paths
    for profile in profiles:
        if profile.endswith('.uml'):
            # its a filename ending with .uml, so lets make it absolute if
            # necessary 
            if not os.path.isabs(profile):
                profile = os.path.join(localdir, profile)
            res.append(profile)
        else:
            # its a profile name, so get the abs path from the config
            res.append(profdict[profile])
    return res


def create_model(targetdir, templatename, modelname):
    confloader = getUtility(IConfLoader)
    settings = confloader.templates_dict[templatename]
    if not os.path.exists(targetdir):
        os.mkdir(targetdir)
    path = settings['path']
    files = os.listdir(path)
    for file in settings['files']:
        buf = open(os.path.join(path,file)).read()
        # fix model references due to renaming
        if file.endswith('.notation'):
            buf = buf.replace('model.uml', modelname + '.uml')
        if file.endswith('.di'):
            buf = buf.replace('model.notation', modelname + '.notation')
        open(os.path.join(targetdir,
                          file.replace('model', modelname)), 'w').write(buf)
    agx = modelname + '.uml.agx'
    profiles = read_config(targetdir, agx)[0]
    #load the profiles
    agx_export(os.path.join(targetdir, agx), profiles)


def run():
    """AGX main routine.
    """
    import agx.core.loader
    starttime = time()
    options, args = parse_options()
    if options.listprofiles != 'unset':
        avaliable_profiles()
        return
    if options.info != 'unset':
        agx_info()
        return
    if options.listtemplates != 'unset':
        avaliable_templates(options.short_messages != 'unset')
        return
    # Create the model from a template
    if options.create_model:
        if args:
            modelname = args[0]
        else:
            modelname = 'model'
        if options.outdir:
            targetdir = options.outdir
        else:
            targetdir = '.'
        templatename = options.create_model
        create_model(targetdir, templatename, modelname)
        return
    if len(args) != 1:
        log.critical("No control flags given.")
        parser.print_help()
        sys.exit(2)
    if options.export != '':
        agx_export(args[0], options.export.split(';'))
        return
    log.info(ARCHGENXML_VERSION_LINE, version())
    log.info('Generator started at %s.' % (
             strftime("%H:%M:%S %Y-%m-%d", gmtime())))
    XMLConfig('configure.zcml', agx.core)()
    modelpath = args[0]
    modelprofiles = options.profiles.strip()
    agxprofiles = []
    agxtarget = []
    localdir, umlname, agxname = prepare_model_path(modelpath)
    umlpath = os.path.join(localdir, umlname)
    if agxname:
        agxprofiles, agxtarget = read_config(localdir, agxname)
    if modelprofiles:
        modelprofiles = re.split('[;,]', modelprofiles)
    else:
        modelprofiles = agxprofiles
    profilepaths = unify_profile_paths(localdir, modelprofiles)
    # XXX: the following 2 lines must be removed when the hardcoded path
    # is fixed in agx.eclipse
#    if options.outdir == '.':
#        options.outdir = localdir

    outdir = options.outdir or localdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    log.info('generating model: %s' % umlpath)
    log.info('using profiles: %s' % profilepaths)
    log.info('generating into: %s' % outdir)
    modelpaths = [umlpath] + profilepaths
    controller = agx.core.Controller()
    controller(modelpaths, outdir)
    log.info('Generator run took %1.2f sec.' % (time() - starttime))
