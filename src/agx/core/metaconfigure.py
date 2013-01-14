from zope.component import (
    provideUtility,
    getUtility,
)
from zope.component.zcml import utility
from zope.component.interfaces import ComponentLookupError
from zope.configuration.exceptions import ConfigurationError
from agx.core.interfaces import (
    ITransform, 
    IGenerator, 
    IDispatcher, 
    IScope, 
    ITargetHandler, 
    IHandler, 
)
from agx.core import (
    Generator,
    Dispatcher,
    Scope,
    NullTargetHandler,
    Handler,
)
from agx.core.util import normalizetext


def _chkregistered(iface, name=None):
    try:
        getUtility(iface, name=name)
        msg = u"``%s`` was already registered by name '%s'"
        msg = msg % (str(iface), str(name))
        raise ConfigurationError(msg)
    except ComponentLookupError, e:
        pass


def registerTransform(name, class_):
    _chkregistered(ITransform, name=name)
    transform = class_(name)
    provideUtility(transform, provides=ITransform, name=name)


def transformDirective(_context, name, class_):
    transform = class_(name)
    utility(_context, provides=ITransform,
            component=transform, name=name)


def registerGenerator(name, transform, depends,
                      targethandler=NullTargetHandler,
                      dispatcher=Dispatcher, class_=Generator,
                      description=u''):
    name = '%s.%s' % (transform, name)
    _chkregistered(IGenerator, name=name)
    _chkregistered(IDispatcher, name=name)
    _chkregistered(ITargetHandler, name=name)
    description = normalizetext(description)
    generator = class_(name, depends, description)
    provideUtility(generator, provides=IGenerator, name=name)
    dispatcher = dispatcher(name)
    provideUtility(dispatcher, provides=IDispatcher, name=name)
    targethandler = targethandler(None)
    provideUtility(targethandler, provides=ITargetHandler, name=name)


def generatorDirective(_context, name, transform, depends,
                       targethandler=NullTargetHandler,
                       dispatcher=Dispatcher, class_=Generator,
                       description=u''):
    name = '%s.%s' % (transform, name)
    description = normalizetext(description)
    generator = class_(name, depends, description)
    utility(_context, provides=IGenerator, component=generator, name=name)
    dispatcher = dispatcher(name)
    utility(_context, provides=IDispatcher, component=dispatcher, name=name)
    targethandler = targethandler(None)
    utility(_context, provides=ITargetHandler,
            component=targethandler, name=name)


def registerScope(name, transform, interfaces, class_=Scope):
    name = '%s.%s' % (transform, name)
    _chkregistered(IScope, name=name)
    scope = class_(name, interfaces)
    provideUtility(scope, provides=IScope, name=name)


def scopeDirective(_context, name, transform, interfaces, class_=Scope):
    name = '%s.%s' % (transform, name)
    scope = class_(name, interfaces)
    utility(_context, provides=IScope, component=scope, name=name)


def registerHandler(name, transform, generator, scope,
                    order=-1, class_=None, attribute=None):
    if attribute and class_:
        msg = u"Either ``class`` or ``attribute`` must be set."
        raise ConfigurationError(msg)
    name = '%s.%s.%s' % (transform, generator, name)
    _chkregistered(IHandler, name=name)
    handler = class_(name, scope, order)
    provideUtility(handler, provides=IHandler, name=name)


def handlerDirective(_context, name, transform, generator,
                     scope, class_=None, attribute=None, order=-1):
    if attribute and class_:
        msg = u"Either ``class`` or ``attribute`` must be set."
        raise ConfigurationError(msg)
    name = '%s.%s.%s' % (transform, generator, name)
    handler = class_(name, scope, order)
    utility(_context, provides=IHandler, component=handler, name=name)


class handler(object):
    """Handler decorator.
    """

    def __init__(self, name, transform, generator, scope,
                 order=-1, class_=Handler):
        self.name = name
        self.transform = transform
        self.generator = generator
        self.scope = scope
        self.order = order
        self.class_ = class_

    def __call__(self, ob):
        name = '%s.%s.%s' % (self.transform, self.generator, self.name)
        _chkregistered(IHandler, name=name)
        handler = self.class_(name, self.scope, self.order)
        handler.__dict__['_callfunc'] = ob
        provideUtility(handler, provides=IHandler, name=name)
        return ob
