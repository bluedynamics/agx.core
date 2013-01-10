import os
import subprocess
from zope.interface import implementer
from zope.configuration.xmlconfig import XMLConfig
from agx.core.interfaces import IConfLoader


# generators registry
generators = list()


def register_generator(package):
    generators.append(package)


@implementer(IConfLoader)
class ConfLoader(object):
    flavour = 'Develop'
    transforms = [
        'xmi2uml',
        'uml2fs']

    @property
    def generators(self):
        ret = list()
        cmd = 'git rev-parse --verify HEAD'
        for generator in generators:
            directory = os.path.split(generator.__file__)
            while directory[1] != 'src':
                directory = os.path.split(directory[0])
            os.chdir(directory[0])
            p = subprocess.Popen(
                cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
            output = p.stdout.readlines()
            version = output[0].strip('\n')
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

    def __call__(self):
        for generator in generators:
            XMLConfig('configure.zcml', generator)()
