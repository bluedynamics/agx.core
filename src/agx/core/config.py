import os
import subprocess
import ConfigParser
import pkg_resources
from StringIO import StringIO

from zope.interface import implementer
from zope.configuration.xmlconfig import XMLConfig
from agx.core.interfaces import IConfLoader


# generators registry
generators = list()


def register_generator(package):
    generators.append(package)


@implementer(IConfLoader)
class ConfLoader(object):
    flavour = 'Reincarnation'  # XXX: rename ``flavour`` to ``code_name``
    transforms = [
        'xmi2uml',
        'uml2fs']

    @property
    def generators(self):
        ret = list()
        for generator in generators:
            name = generator.__name__
            version = pkg_resources.get_distribution(name).version
            ret.append((generator.__name__, version))
        return ret

    @property
    def profiles(self):
        ret = list()
        for generator in generators:
            for profile in self._profiles(generator):
                ret.append(profile)
        return ret

    def _profiles(self, module):
        basepath = os.path.split(module.__file__)[:-1][0]
        profilepath = os.path.join(basepath, 'profiles')
        ret = list()
        if os.path.exists(profilepath) and os.path.isdir(profilepath):
            for file in os.listdir(profilepath):
                if file.endswith('uml'):
                    ret.append([
                        file[0:file.find('.profile.uml')],
                        os.path.join(profilepath, file),
                    ])
        return ret

    def open_manifest(self, templpath, fname='manifest.txt'):
        """Parses the manifest.
        """
        res = {
            'modelname': 'model',
            'title': os.path.split(templpath)[-1],
            'description': '',
        }
        buf = '[default]\n' + open(os.path.join(templpath, fname)).read()
        cp = ConfigParser.SafeConfigParser()
        cp.readfp(StringIO(buf))
        res['files'] = \
            [f for f in cp.get('default', 'files').strip().replace('\n', '')\
                .replace('\\', '').split(';') if f]
        if cp.has_option('default', 'modelname'):
            res['modelname'] = cp.get('default', 'modelname')
        if cp.has_option('default', 'title'):
            res['title'] = cp.get('default', 'title')
        if cp.has_option('default', 'description'):
            res['description'] = cp.get('default', 'description')
        return res

    @property
    def templates(self):
        ret = list()
        tempdict = self.templates_dict
        for k in tempdict:
            r = tempdict[k]
            ret.append([r['name'], r['title'], r['description'],r['path']])
        return ret

    @property
    def templates_dict(self):
        ret = {}
        for generator in generators:
            tempdict = self._templates_dict(generator)
            ret.update(tempdict)
        return ret

    def _templates_dict(self, module):
        basepath = os.path.split(module.__file__)[:-1][0]
        respath = os.path.join(basepath, 'resources')
        ret = {}
        if os.path.exists(respath) and os.path.isdir(respath):
            templpath = os.path.join(respath, 'model_templates')
            if os.path.exists(templpath) and os.path.isdir(templpath):
                for file in os.listdir(templpath):
                    conf = self.open_manifest(os.path.join(templpath, file))
                    ret[file] = {
                        'name': file,
                        'title': conf['title'],
                        'files': conf['files'],
                        'description': conf['description'],
                        'path': os.path.join(templpath, file),
                    }
        return ret

    def __call__(self):
        for generator in generators:
            XMLConfig('configure.zcml', generator)()
