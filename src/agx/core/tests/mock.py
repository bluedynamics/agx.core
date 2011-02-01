# Copyright BlueDynamics Alliance - http://bluedynamics.com
# GNU General Public License Version 2

from zope.interface import implements
from zope.interface import alsoProvides

###############################################################################   
# IO related
###############################################################################

from plumber import plumber
from node.parts import (
    Adopt,
    NodeChildValidate,
    Nodespaces,
    Attributes,
    DefaultInit,
    Nodify,
    Reference,
    Order,
    OdictStorage,
)

class Node(object):
    __metaclass__ = plumber
    __plumbing__ = (
        Adopt,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        DefaultInit,
        Nodify,
        Reference,
        Order,
        OdictStorage,
    )

from agx.core.interfaces import ISource

class SourceMock(Node):
    implements(ISource)
  
from agx.core.interfaces import ITarget

class TargetMock(Node):
    implements(ITarget)
    
    def __call__(self):
        print '``__call__()`` of %s' % '.'.join(self.path)
        for child in self:
            child()

###############################################################################   
# Transform related
###############################################################################

from node.interfaces import IRoot
from agx.core.interfaces import ITransform

class TransformMock(object):
    implements(ITransform)
    
    def __init__(self, name):
        self.name = name
        self._source = SourceMock('root')
        self._target = TargetMock('root')
        
    def source(self, path):
        return self._source
           
    def target(self, path):
        return self._target

###############################################################################   
# Generator related
###############################################################################

from agx.core import TargetHandler

class TargetHandlerMock(TargetHandler):
    
    def __call__(self, source):
        self.setanchor(source.path)
