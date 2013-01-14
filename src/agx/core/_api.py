import types
from odict import odict
from node.interfaces import IRoot
from zope.interface import implementer
from zope.component import (
    getUtility,
    getUtilitiesFor,
    provideUtility,
)
from zope.component.interfaces import ComponentLookupError
from agx.core.interfaces import (
    IConfLoader,
    IController,
    IProcessor,
    ITransform,
    IGenerator,
    ITargetHandler,
    IDispatcher,
    IHandler,
    IScope,
    IToken,
)
from agx.core.util import (
    readsourcepath,
    writesourcepath,
    write_source_to_target_mapping,
)


@implementer(IController)
class Controller(object):
    """AGX standalone main controller.
    """

    def __call__(self, sourcepath, targetpath):
        confloader = getUtility(IConfLoader) 
        confloader()
        source = None
        target = None
        for name in confloader.transforms:
            transform = getUtility(ITransform, name=name)
            source = transform.source(sourcepath)
            if source is None:
                # case continuation, expects None from transform.source
                source = target
            target = transform.target(targetpath)
            processor = Processor(name)
            target = processor(source, target)
        target()
        return target


@implementer(IProcessor)
class Processor(object):
    """Default processor.
    """

    def __init__(self, transform):
        """@param transform: The transform name
        """
        self.transform = transform

    def __call__(self, source, target):
        generators = self.lookup_generators()
        targethandler = None
        for generator in generators:
            targethandler = getUtility(ITargetHandler, name=generator.name)
            targethandler.anchor = None
            targethandler.__init__(target)
            generator(source, targethandler)
        if targethandler is None:
            # no generators registered:
            return target
        return targethandler.anchor.root

    def lookup_generators(self):
        generators = list()
        for genname, generator in getUtilitiesFor(IGenerator):
            transformname = genname[:genname.find('.')]
            if transformname == self.transform:
                generators.append(generator)
        generators = self._sortgenerators(generators)
        return generators

    def _sortgenerators_j(self, generators):
        # jensens flavor of a valid dependency chain sorter
        # it breaks the test, nevertheless its output is valid
        lookup = odict([(g.name[g.name.find('.')+1:], g) for g in generators])
        inkeys = lookup.keys()
        outkeys = ['NO']
        while len(inkeys) != 0:
            iterkeys = [k for k in inkeys]
            for inkey in iterkeys:
                if lookup[inkey].depends not in outkeys:
                    continue
                outkeys.insert(outkeys.index(lookup[inkey].depends)+1, inkey)
                inkeys.remove(inkey)
            if len(iterkeys) == len(inkeys):
                raise ValueError, 'Broken dependency chain.'
        return [lookup[key] for key in outkeys[1:]]

    def _sortgenerators_r(self, generators):
        dtree = {'NO': ([], {})}
        self._makedtree(generators, dtree)
        sortedgen = list()
        self._fillsorted(sortedgen, dtree)
        return sortedgen

    _sortgenerators = _sortgenerators_r

    def _fillsorted(self, sortedgen, dtree):
        """Flatten dependency tree.
        """
        for key in sorted(dtree.keys()):
            for gen in dtree[key][0]:
                sortedgen.append(gen)
            self._fillsorted(sortedgen, dtree[key][1])

    def _makedtree(self, generators, dtree):
        """Sort list of generators by generator.dependency.
        """
        children = list()
        for generator in generators:
            if not generator.depends in dtree.keys():
                children.append(generator)
                continue
            genname = generator.name[generator.name.find('.') + 1:]
            if dtree[generator.depends][1].get(genname, None) is None:
                dtree[generator.depends][1][genname] = ([], {})
            for gen in dtree[generator.depends][0]:
                if gen.name == generator.name:
                    continue
            dtree[generator.depends][0].append(generator)
                
        for child in dtree.values():
            self._makedtree(children, child[1])

    def _printdtree(self, dtree, indent=0):
        """Debug function.
        """
        keys = dtree.keys()
        keys.sort()
        for key in keys:
            if dtree[key][1].keys():
                print indent * ' ' + '%s dependencies:' % key
            for gen in dtree[key][0]:
                print (indent) * ' ' + ' - %s' % gen.name
            self._printdtree(dtree[key][1], indent + 4)


@implementer(IGenerator)
class Generator(object):
    """Default Generator.
    """

    def __init__(self, name, depends, description=u''):
        self.name = name
        self.depends = depends
        self.description = description
        self.backup = False

    def __call__(self, source, target):
        self.source = source
        self.target = target
        self._dispatch([source])

    def _dispatch(self, children):
        dispatcher = getUtility(IDispatcher, name=self.name)
        for child in children:
            self.target(child)            
            dispatcher(child, self.target)
            self._dispatch([node for name, node in child.items()])


@implementer(ITargetHandler)
class TargetHandler(object):
    """Abstract target handler.
    """
    anchor = None

    def __init__(self, root):
        self.target = root
        if self.anchor is None:
            self.anchor = root

    def __call__(self, source):
        raise NotImplementedError(u"Abstract target handler does not "
                                   "implement ``__call__``.")

    def setanchor(self, path):
        node = self.target
        self._setanchor([node], path)

    def _setanchor(self, children, path):
        name = path[0]
        for child in children:
            if name == child.__name__:
                if len(path) > 1:
                    self._setanchor(child.values(), path[1:])
                else:
                    self.anchor = child
                return
        raise KeyError(u"Target node does not exist.")


class NullTargetHandler(TargetHandler):
    """A target handler which does nothing.
    
    Used as default target handler if no one is defined for a generator.
    """

    def __call__(self, source):
        pass


class TreeSyncPreperator(TargetHandler):
    """Sync anchor by sourcepath.
    """

    def __call__(self, source):
        if len(source.path) <= len(readsourcepath(self.anchor)):
            elem = self.anchor
            while len(readsourcepath(elem)) >= len(source.path):
                elem = elem.__parent__
            self.anchor = elem

    def finalize(self, source, target, set_anchor=True):
        writesourcepath(source, target)
        write_source_to_target_mapping(source, target)
        if set_anchor:
            self.anchor = target


@implementer(IScope)
class Scope(object):
    """Scope mapping against interfaces.
    """

    def __init__(self, name, interfaces):
        if not type(interfaces) == types.ListType:
            interfaces = [interfaces]
        self.name = name
        self.interfaces = interfaces

    def __call__(self, node):
        for iface in self.interfaces:
            if iface.providedBy(node):
                return True
        return False


@implementer(IDispatcher)
class Dispatcher(object):
    """Default dispatcher.
    """

    def __init__(self, generator):
        self.generator = self.name = generator
        self.transform = generator[:generator.find('.')]

    def __call__(self, source, targethandler):
        handlers = self.lookup_handlers()
        for handler in handlers:
            if handler.scope:
                scopename = '%s.%s' % (self.transform, handler.scope)
                scope = getUtility(IScope, name=scopename)
                if not scope(source):
                    continue
            handler(source, targethandler)

    def lookup_handlers(self):
        handlers = getUtilitiesFor(IHandler)
        handlers = [util for name, util in handlers]
        unordered = list()
        for handler in handlers:
            if handler.order == -1:
                unordered.append(handler)
        handlers = [handler for handler in handlers if handler.order > -1]
        handlers.sort(lambda x, y: x.order < y.order and -1 or 1)
        handlers = handlers + unordered
        handlers = [handler for handler in handlers \
                    if handler.name.startswith(self.name)]
        return handlers


@implementer(IHandler)
class Handler(object):
    """Base handler, can be registered by ``@handler`` decorator.
    """

    def __init__(self, name, scope, order):
        self.name = name
        self.scope = scope
        self.order = order
        self._callfunc = None

    def __call__(self, source, target):
        self._callfunc(self, source, target)


def token(name, create, reset=False, **kw):
    """Create or lookup a token by name.
    """
    if type(name) is types.ListType:
        name = '.'.join(name)
    kw['name'] = name
    try:
        token = getUtility(IToken, name=name)
        if reset:
            token.__init__(**kw)
        for k in kw:
            if not hasattr(token, k): setattr(token, k, kw[k])
    except ComponentLookupError, e:
        if not create:
            raise e
        token = Token(**kw)
        provideUtility(token, provides=IToken, name=name)
    return token


@implementer(IToken)
class Token(object):
    """A token.
    """

    def __init__(self, **kw):
        self.__dict__.update(kw)
