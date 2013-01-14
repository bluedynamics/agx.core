from zope.interface import implementer
from zope.interface import alsoProvides


###############################################################################   
# IO related
###############################################################################


from plumber import plumber
from node.behaviors import (
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


@implementer(ISource)
class SourceMock(Node):
    pass
  
  
from agx.core.interfaces import ITarget


@implementer(ITarget)
class TargetMock(Node):

    def __call__(self):
        print '``__call__()`` of %s' % '.'.join(self.path)
        for child in self:
            child()


###############################################################################   
# Transform related
###############################################################################


from node.interfaces import IRoot
from agx.core.interfaces import ITransform


@implementer(ITransform)
class TransformMock(object):

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
