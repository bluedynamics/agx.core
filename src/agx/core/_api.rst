API
===

``agx.core`` contains model transformation chain processor, the corresponding
implementations and classes, registration helpers and common utils.


Controller
----------

The controller is created and called by the main script.

It expects a registered ``agx.core.interfaces.IConfLoader`` implementing
utility. This is responsible to load the desired transforms and generators::

    >>> from zope.interface import implementer
    >>> from zope.component import provideUtility
    >>> from agx.core.interfaces import IConfLoader
    >>> @implementer(IConfLoader)
    ... class LoaderMock(object):
    ...     transforms = ['mock']
    ...     def __call__(self): pass
    >>> loader = LoaderMock()
    >>> provideUtility(loader, provides=IConfLoader)

At least one transform must be registered by a unique name::

    >>> from agx.core import registerTransform
    >>> from agx.core.testing.mock import TransformMock
    >>> registerTransform(name='mock', class_=TransformMock)

This transform provides ``agx.core.interfaces.ISource`` and
``agx.core.interfaces.ITarget`` implementations.

Register some generators to test generator execution and dependency chain::

    >>> from agx.core import registerGenerator
    >>> from agx.core import Generator
    >>> from agx.core.testing.mock import TargetHandlerMock
    >>> class NullGenerator(Generator):
    ...     def __call__(self, source, target):
    ...         print 'generator: %s' % self.name
    ...         print 'depends: %s' % self.depends
    ...         print 40 * '-'
    >>> registerGenerator(name='generator-1',
    ...                   transform='mock',
    ...                   depends='NO',
    ...                   targethandler=TargetHandlerMock,
    ...                   class_=NullGenerator)
    >>> registerGenerator(name='generator-2',
    ...                   transform='mock',
    ...                   depends='NO',
    ...                   targethandler=TargetHandlerMock,
    ...                   class_=NullGenerator)
    >>> registerGenerator(name='generator-3',
    ...                   transform='mock',
    ...                   depends='generator-1',
    ...                   targethandler=TargetHandlerMock,
    ...                   class_=NullGenerator)
    >>> registerGenerator(name='generator-4',
    ...                   transform='mock',
    ...                   depends='generator-1',
    ...                   targethandler=TargetHandlerMock,
    ...                   class_=NullGenerator)
    >>> registerGenerator(name='generator-5',
    ...                   transform='mock',
    ...                   depends='generator-2',
    ...                   targethandler=TargetHandlerMock,
    ...                   class_=NullGenerator)

The controller iterates through the generators when its called. For each
generator a the target handler is looked up and initialized with the source
root::

    >>> from agx.core import Controller
    >>> controller = Controller()
    >>> controller(sourcepath=None, targetpath=None)
    generator: mock.generator-1
    depends: NO
    ----------------------------------------
    generator: mock.generator-2
    depends: NO
    ----------------------------------------
    generator: mock.generator-3
    depends: generator-1
    ----------------------------------------
    generator: mock.generator-4
    depends: generator-1
    ----------------------------------------
    generator: mock.generator-5
    depends: generator-2
    ----------------------------------------
    ``__call__()`` of root
    <TargetMock object 'root' at ...>

Overwrite loader and Register the mock transform with another name for later
tests::

    >>> @implementer(IConfLoader)
    ... class LoaderMock(object):
    ...     transforms = ['mock2mock']
    ...     def __call__(self): pass
    >>> loader = LoaderMock()
    >>> provideUtility(loader, provides=IConfLoader)
    >>> registerTransform(name='mock2mock', class_=TransformMock)


Generator
---------

A Generator is responsible to call its target handler for each source element
of the model and then its dispatcher with this source and the target anchor set
or created by target handler.

We need a mock model::

    >>> from agx.core.testing.mock import Node
    >>> from agx.core.interfaces import ITarget
    >>> @implementer(ITarget)
    ... class TargetMock(Node):
    ...     def __call__(self): pass
  
    >>> target = TargetMock('root')
    >>> target['child1'] = TargetMock()
    >>> target['child1']['sub1'] = TargetMock()
    >>> target['child1']['sub2'] = TargetMock()
    >>> target['child2'] = TargetMock()
    >>> target['child2']['sub1'] = TargetMock()

In this case we operate on an existing target model. Of course, AGX also allows
building a target model from scratch.

Mark root::

    >>> from zope.interface import alsoProvides
    >>> from node.interfaces import IRoot
    >>> alsoProvides(target, IRoot)
    >>> IRoot.providedBy(target)
    True

    >>> IRoot.providedBy(target['child1'])
    False


TargetHandler
-------------

A target handler is used to prepare the target which is given to the handler.
This is useful, since the target tree is normally not synchronous to the source
tree, and handlers might just want to add nodes to a predefined container.

if a generator is registered without a specific targethandler, the
``NullTargetHandler`` object is instanciated and used for this generator, which
does nothing with the target and leaves the containment handling to the
registered handlers for this generator. 

The target handler base class is supposed to be used for the generator specific
target handler. It implements the signature but not the ``call`` method::

    >>> from agx.core import TargetHandler
    >>> targethandler = TargetHandler(target)

Call is not implemented::

    >>> targethandler(Node())
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract target handler does not implement ``__call__``.

Test setanchor function::

    >>> targethandler.setanchor(['root', 'child2', 'sub1'])
    >>> targethandler.anchor.path
    ['root', 'child2', 'sub1']

    >>> targethandler.setanchor(['root', 'child1'])
    >>> targethandler.anchor.path
    ['root', 'child1']

    >>> targethandler.setanchor(['root', 'child3'])
    Traceback (most recent call last):
      ...
    KeyError: u'Target node does not exist.'

    >>> targethandler.setanchor(['root', 'child2', 'sub2'])
    Traceback (most recent call last):
      ...
    KeyError: u'Target node does not exist.'

The existing mock target handler does a 1:1 mapping between source and target
on synchronous and existing models::

    >>> from agx.core.testing.mock import TargetHandlerMock
    >>> targethandler = TargetHandlerMock(target)
    >>> targethandler.anchor.path
    ['root']

    >>> from copy import copy
    >>> source = target
    >>> targethandler(source['child1']['sub2'])
    >>> targethandler.anchor.path
    ['root', 'child1', 'sub2']

For generator testing purposes we cave the default dispatcher a little bit::

    >>> from agx.core import Dispatcher
    >>> class DispatcherMock(Dispatcher):
    ...     def __call__(self, source, target):
    ...         print 'source: ' + str(source.path)
    ...         print 'target: ' + str(target.anchor.path)

Register a generator. The refering dispatcher and target handler are registered
here as well under the same name as the generator::

    >>> from agx.core import registerGenerator
    >>> from agx.core import Generator
    >>> registerGenerator(name='mockgenerator',
    ...                   transform='mock2mock',
    ...                   depends='NO',
    ...                   targethandler=TargetHandlerMock,
    ...                   dispatcher=DispatcherMock,
    ...                   class_=Generator)

Lookup the generator. The name of the generator is combined out of transform
name and generator name::

    >>> from zope.component import getUtility
    >>> from agx.core.interfaces import IGenerator
    >>> generator = getUtility(IGenerator, name='mock2mock.mockgenerator')
    >>> generator
    <agx.core._api.Generator object at ...>

    >>> generator.name
    'mock2mock.mockgenerator'

    >>> from agx.core.interfaces import IDispatcher
    >>> getUtility(IDispatcher, name='mock2mock.mockgenerator')
    <DispatcherMock object at ...>

    >>> from agx.core.interfaces import ITargetHandler
    >>> getUtility(ITargetHandler, name='mock2mock.mockgenerator')
    <agx.core.testing.mock.TargetHandlerMock object at ...>

    >>> generator(source, targethandler)
    source: ['root']
    target: ['root']
    source: ['root', 'child1']
    target: ['root', 'child1']
    source: ['root', 'child1', 'sub1']
    target: ['root', 'child1', 'sub1']
    source: ['root', 'child1', 'sub2']
    target: ['root', 'child1', 'sub2']
    source: ['root', 'child2']
    target: ['root', 'child2']
    source: ['root', 'child2', 'sub1']
    target: ['root', 'child2', 'sub1']


Scopes
------

A Scope is used by the dispatcher to check whether a source element should be
processed or not. This is done due to interfaces provided by the source node.
A scope is bound to a transform::

    >>> from agx.core import registerScope
    >>> from zope.interface import Interface
    >>> class IFoo(Interface):
    ...     """Marker for ``foo`` node.
    ...     """
    >>> class IBar(Interface):
    ...     """Marker for ``foo`` node.
    ...     """

    >>> registerScope('foo', 'mock2mock', IFoo)
    >>> registerScope('bar', 'mock2mock', IBar)
    >>> registerScope('foobar', 'mock2mock', [IFoo, IBar])
    >>> registerScope('all', 'mock2mock', Interface)
    >>> from agx.core.interfaces import IScope
    >>> from zope.component import getUtilitiesFor
    >>> scopes = getUtilitiesFor(IScope)
    >>> scopes = [name for name, util in scopes]
    >>> scopes.sort()

Note that u'mocktransform.dummyscope' was registered due ZCML tests::

    >>> len(scopes) > 0
    True

Mark some source node to be either IFoo or IBar::

    >>> from zope.interface import alsoProvides
    >>> alsoProvides(source['child1'], IFoo)
    >>> alsoProvides(source['child2']['sub1'], IFoo)
    >>> alsoProvides(source['child2']['sub1'], IBar)

Check if scope object works as expected::

    >>> barscope = getUtility(IScope, name=u'mock2mock.bar')
    >>> barscope(source)
    False

    >>> barscope(source['child2']['sub1'])
    True


Handlers
--------

While a target handler is responsible to provide transform specific general
target handling, i.e. map XMI packages to filesystem directories and create
target nodes for them if required, the handler implementations know about the
details.

They read and write tokens, acquire information from the source tree, create
target leafs, i.e. templates and contain the business logic.

A handler is registered for a transform and a generator by a name. The name
of a handler must be unique inside its namespace
``'transformname.generatorname.*'``.

A handler could be bound to a scope and you can define the execution order of
handlers inside its generator::

    >>> from agx.core import Handler
    >>> class HandlerMock(Handler):
    ...     def __call__(self, source, target):
    ...         print 40 * '-'
    ...         print 'handler: %s' % self.name
    ...         print 'path: %s' % source.path
    ...         print 'order: %s' % self.order

    >>> from agx.core import registerHandler
    >>> registerHandler(name='nullhandler',
    ...                 transform='mock2mock',
    ...                 generator='testgenerator',
    ...                 scope=None,
    ...                 class_=HandlerMock,
    ...                 attribute=None,
    ...                 order=-1)

    >>> from agx.core.interfaces import IHandler
    >>> getUtility(IHandler, name='mock2mock.testgenerator.nullhandler')
    <HandlerMock object at ...>

We don't want to subclass the handler every time, so we provide a decorator for
convenience::

    >>> from agx.core import handler

    >>> @handler('foohandler', 'mock2mock', 'testgenerator', 'foo', 4)
    ... def foohandler(self, source, target):
    ...     print 40 * '-'
    ...     print 'handler: %s' % self.name
    ...     print 'path: %s' % source.path
    ...     print 'order: %s' % self.order
    ...     print 'IFoo provided: %s' % str(IFoo.providedBy(source))

    >>> foohandler = getUtility(IHandler,
    ...              name='mock2mock.testgenerator.foohandler')
    >>> foohandler._callfunc
    <function foohandler at ...>

Register some more handlers for dispatcher testing::

    >>> @handler('barhandler', 'mock2mock', 'testgenerator', 'bar', 3)
    ... def barhandler(self, source, target):
    ...     print 40 * '-'
    ...     print 'handler: %s' % self.name
    ...     print 'path: %s' % source.path
    ...     print 'order: %s' % self.order
    ...     print 'IBar provided: %s' % str(IBar.providedBy(source))

    >>> @handler('foobarhandler', 'mock2mock', 'testgenerator', 'foo', 2)
    ... def foobarhandler(self, source, target):
    ...     print 40 * '-'
    ...     print 'handler: %s' % self.name
    ...     print 'path: %s' % source.path
    ...     print 'order: %s' % self.order
    ...     print 'IFoo and IBar provided: %s %s' % (str(IFoo.providedBy(source)),
    ...                                              str(IBar.providedBy(source)))

    >>> @handler('interfacehandler', 'mock2mock', 'testgenerator', 'all', 1)
    ... def ifacehandler(self, source, target):
    ...     print 40 * '-'
    ...     print 'handler: %s' % self.name
    ...     print 'path: %s' % source.path
    ...     print 'order: %s' % self.order
    ...     print 'interface provided'


Dispatcher
----------

The dispatcher is responsible to lookup handlers for the generator namespace,
check the source node against the scope if defined and execute the handlers in
a defined order.

If an order is not defined, the referring handlers are executed after those with
a defined order.

Define our test source and target models on the already registered transform
mock (where we have all our stuff bound to)::

    >>> from agx.core.interfaces import ITransform
    >>> transform = getUtility(ITransform, name='mock2mock')
    >>> transform._source = source
    >>> transform._target = target

Define another mockgenerator that it uses the default dispatcher::

    >>> registerGenerator(name='testgenerator',
    ...                   transform='mock2mock',
    ...                   depends='NO',
    ...                   targethandler=TargetHandlerMock)

And call the mock controller again. Note that 2 generators are executed now.
The 'mockgenerator' and the 'testgenerator' for transform 'mock2mock'::

    >>> controller(None, None)
    source: ['root']
    target: ['root']
    source: ['root', 'child1']
    target: ['root', 'child1']
    source: ['root', 'child1', 'sub1']
    target: ['root', 'child1', 'sub1']
    source: ['root', 'child1', 'sub2']
    target: ['root', 'child1', 'sub2']
    source: ['root', 'child2']
    target: ['root', 'child2']
    source: ['root', 'child2', 'sub1']
    target: ['root', 'child2', 'sub1']
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root']
    order: -1
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root', 'child1']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.foobarhandler
    path: ['root', 'child1']
    order: 2
    IFoo and IBar provided: True False
    ----------------------------------------
    handler: mock2mock.testgenerator.foohandler
    path: ['root', 'child1']
    order: 4
    IFoo provided: True
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root', 'child1']
    order: -1
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root', 'child1', 'sub1']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root', 'child1', 'sub1']
    order: -1
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root', 'child1', 'sub2']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root', 'child1', 'sub2']
    order: -1
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root', 'child2']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root', 'child2']
    order: -1
    ----------------------------------------
    handler: mock2mock.testgenerator.interfacehandler
    path: ['root', 'child2', 'sub1']
    order: 1
    interface provided
    ----------------------------------------
    handler: mock2mock.testgenerator.foobarhandler
    path: ['root', 'child2', 'sub1']
    order: 2
    IFoo and IBar provided: True True
    ----------------------------------------
    handler: mock2mock.testgenerator.barhandler
    path: ['root', 'child2', 'sub1']
    order: 3
    IBar provided: True
    ----------------------------------------
    handler: mock2mock.testgenerator.foohandler
    path: ['root', 'child2', 'sub1']
    order: 4
    IFoo provided: True
    ----------------------------------------
    handler: mock2mock.testgenerator.nullhandler
    path: ['root', 'child2', 'sub1']
    order: -1
    <TargetMock object 'root' at ...>


Tokens
======

Tokens are used to communicate between different generators and handlers,
and/or collect data for final target writing.

A generator might define the contract that some data must be written to a
specific token. the target node reads from this for writing::

    >>> from agx.core import token
    >>> tok = token('foobar', True, foo=Node('foo'), bar=Node('bar'))
    >>> tok
    <agx.core._api.Token object at ...>

    >>> tok.foo
    <Node object 'foo' at ...>

    >>> tok.bar
    <Node object 'bar' at ...>

    >>> tok.bar['data'] = Node('data')

    now get an existing token and verify that extra parameters get added to it
    >>> tok = token('foobar', True, baz='SomeString')
    >>> tok.baz
    'SomeString'

Change a value of the token::

    >>> tok.foo = 'foochanged'

Read token again::

    >>> tok1 = token('foobar', False)
    >>> tok1.foo
    'foochanged'

Read previously added data::

    >>> tok1.bar['data']
    <Node object 'data' at ...>

Reset the token::

    >>> tok2 = token('foobar', False, reset=True, foo=None, bar=None)
    >>> tok2.foo

    >>> tok2.bar

Read token for a specific path::

    >>> tok3 = token(target['child2']['sub1'].path, True)
    >>> tok3.name
    'root.child2.sub1'

Finally try to read an unexisting token::

    >>> tok4 = token('inexistent', False)
    Traceback (most recent call last):
      ...
    ComponentLookupError: (<InterfaceClass agx.core.interfaces.IToken>,
    'inexistent')
