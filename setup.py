# Copyright BlueDynamics Alliance - http://bluedynamics.com
# GNU General Public License Version 2

from setuptools import setup, find_packages
import sys, os

version = open(os.path.join(os.path.dirname(__file__), 'src',
                            'agx', 'core', 'version.txt')).read()
shortdesc = 'AGX tree transformation chain processor'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()

setup(name='agx.core',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
      ],
      keywords='AGX, Code Generation',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url=u'https://svn.plone.org/svn/archetypes/AGX',
      license='GNU General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['agx'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zodict',
          'zope.configuration',
      ],
      extras_require = dict(
          test=[
            'interlude',
          ]
      ),
      )
