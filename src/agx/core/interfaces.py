from zope.interface import (
    Interface,
    Attribute,
)
from zope.interface.common.mapping import (
    IReadMapping,
    IWriteMapping,
    IFullMapping,
)
from node.interfaces import (
    INode,
    ICallable,
)


###############################################################################   
# Core Interfaces
###############################################################################


class IProfileLocation(Interface):
    """Utility interface.
    
    XXX: move to uml related io as soon as the related stuff in main.py gets
         moved.
    """

    name = Attribute(u"UML profile name")
    package = Attribute(u"profile related package.")


class IConfLoader(Interface):
    """Interface to set up the AGX configuration.
    
    This interface is supposed to be implemented by specific generation flavour.
    """

    flavour = Attribute(u"Name for the configuration flavour")

    transforms = Attribute(u"Tranform execution chain as list.")

    profiles = Attribute(u"List of 2-tuples containing available "
                         u"(profilename, profilepath)")

    generators = Attribute(u"List of 2-tuples containing generator name and "
                           u"a unique identifyer for it's version.")

    def __call__():
        """Load required transforms and generators.
        """


class IController(Interface):
    """AGX controller interface.
    """

    def __call__(sourcepath, targetpath):
        """Invoke controller.
        
        @param sourcepath: source path
        @param targetpath: target path
        """


class IProcessor(Interface):
    """AGX processor interface.
    """

    def __call__(source, target):
        """Invoke processor.
        
        @param source: ``agx.core.interfaces.ISource``
        @param target: ``agx.core.interfaces.ITarget``
        """


class ITransform(Interface):
    """Transform interface.
    """

    name = Attribute(u"Name of this transform")

    def source(path):
        """Read source.
        
        @param path: source path.
        @return: ``agx.core.interfaces.ISource`` implementation.
        """

    def target(path):
        """Read target.
        
        @param path: target path.
        @return: ``agx.core.interfaces.ITarget`` implementation.
        """


class IGenerator(Interface):
    """Generator interface.
    """

    name = Attribute(u"The name of this generator")
    depends = Attribute(u"generators this generator depends on")
    backup = Attribute(u"Flag wether generator should create backup or not")

    def __call__(source, target):
        """Walk through source and invoke a dispatcher for each element.
        
        @param source: ``agx.core.interfaces.IRoot`` implementation.
        @param target: ``agx.core.interfaces.ITargetHandler`` implementation.
        """


class IDispatcher(Interface):
    """Dispatcher interface.
    """

    generator = Attribute(u"Generator name.")

    def __call__(source, target):
        """Dispatch handlers for element.
        
        @param source: ``agx.core.interfaces.ISource`` implementation.
        @param target: ``agx.core.interfaces.ITargetHandler`` implementation.
        """


class IScope(Interface):
    """Scope interface.
    """

    name = Attribute(u"Name of this scope")
    interfaces = Attribute(u"List of ``zope.interface.Interface``.")

    def __call__(node):
        """Check wether scope applies on node.
        
        @param node: ``agx.core.interfaces.INode`` implementation.
        @return: bool
        """


class ITargetHandler(Interface):
    """Interface to handle the write target for IHandler implementations.
    
    The implementation of this interface is supposed to provide senceful
    defaults for a generator on ``__call__()`` time, i.e. set or create
    directory targets mapped to UML packages.
    """

    target = Attribute(u"``IRoot``")
    anchor = Attribute(u"The recent ``ITarget`` implementation.")

    def __call__(source):
        """Set ``self.anchor`` refering to given source.
        
        @param source: ``ISource`` implementation.
        """

    def setanchor(path):
        """Set anchor manually by given path.
        
        @param path: list representing the absolute node path.
        """


class IHandler(Interface):
    """Handler interface.
    """

    name = Attribute(u"Name of handler")
    scope = Attribute(u"Name of a scope")
    order = Attribute(u"Execution order. Defaults to -1 if order does not "
                       "matter")

    def __call__(source, target):
        """Dispatch handlers for element.
        
        @param source: ``agx.core.interfaces.ISource`` implementation.
        @param target: ``agx.core.interfaces.ITargetHandler`` implementation.
        """


class IToken(Interface):
    """Token for data collection.
    """

    def __init__(**kw):
        """Everything contained in kw is available through __getitem__
        """

    def __getattribute__(name):
        """Provide access to all given kw args.
        """


###############################################################################
# Model related interfaces.
###############################################################################


class IDataAcquirer(IReadMapping):
    """Interface for acquiring data from ``INode.``
    implementing objects.
    """

    def __getitem__(name):
        """Acquire data from node.
        
        @param name: key of requested data.
        """

    def get(name, default=None, aggregate=False, depth=-1, breakiface=None):
        """Acquire data from node.
        
        @param name: key of requested data.
        @param default: default return value.
        @param aggregate: Flag wether to aggregate requested value.
        @param depth: recurion depth. default ``-1`` is recurion until root.
        @param breakiface: ``zope.Interface`` defining the acquisition break
                           point.
        """


class IDataReader(IReadMapping):
    """Convenience reader interface.
    """

    aq = Attribute(u"``IDataAcquirer`` implementation")

    def keys():
        """Return available keys.
        """


###############################################################################
# IO related interfaces.
###############################################################################


class ISource(INode):
    """Source element.
    """


class ITarget(INode, ICallable):
    """Target Element.
    """
