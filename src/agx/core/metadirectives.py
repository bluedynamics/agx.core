from zope import (
    interface,
    schema,
)
from zope.configuration import fields


class ITransformDirective(interface.Interface):
    """Directive for transforms.
    """

    name = schema.TextLine(
        title=u"Transform name",
        description=u"Name of this transform.",
        required=True)

    class_ = fields.GlobalObject(
        title=u"Transform implementation",
        description=u"``agx.core.interfaces.ITransform`` implementation",
        required=True)


class IGeneratorDirective(interface.Interface):
    """Directive for generators.
    """

    name = schema.TextLine(
        title=u"Generator name",
        description=u"Name of this generator.",
        required=True)

    transform = schema.TextLine(
        title=u"Transform name",
        description=u"Name of the transform this generator works for.",
        required=True)

    depends = schema.TextLine(
        title=u"Dependency generator",
        description=u"Generator expected to already be executed.",
        required=True)

    targethandler = fields.GlobalObject(
        title=u"Target handler implementation",
        description=u"``agx.core.interfaces.ITargetHandler`` implementation",
        required=False)

    dispatcher = fields.GlobalObject(
        title=u"Dispatcher implementation",
        description=u"``agx.core.interfaces.IDispatcher`` implementation",
        required=False)

    class_ = fields.GlobalObject(
        title=u"Generator implementation",
        description=u"``agx.core.interfaces.IGenerator`` implementation",
        required=False)

    description = schema.TextLine(
        title=u"Generator description",
        description=u"Inserted to Sphinx documentation if set.",
        required=False)


class IScopeDirective(interface.Interface):
    """Directive for scopes.
    """

    name = schema.TextLine(
        title=u"Scope name",
        description=u"Name of this scope.",
        required=True)

    transform = schema.TextLine(
        title=u"Transform name",
        description=u"Transform this scope applies.",
        required=True)

    interfaces = fields.Tokens(
        title=u"Interfaces",
        description=u"``zope.interface.Interface``",
        required=True,
        value_type=fields.GlobalInterface())

    class_ = fields.GlobalObject(
        title=u"Scope implementation",
        description=u"``agx.core.interfaces.IScope`` implementation",
        required=False)


class IHandlerDirective(interface.Interface):
    """Directive for handlers.
    """

    name = schema.TextLine(
        title=u"Handler name",
        description=u"Name of this handler.",
        required=True)

    transform = schema.TextLine(
        title=u"Transform name",
        description=u"Name of the transform this handler works for.",
        required=True)

    generator = schema.TextLine(
        title=u"Generator name",
        description=u"Name of the Generator this handler works for.",
        required=True)

    scope = schema.TextLine(
        title=u"Scope name",
        description=u"scope to check.",
        required=True)

    class_ = fields.GlobalObject(
        title=u"``agx.core.interfaces.IHandler`` implementation",
        description=u"",
        required=False)

    attribute = fields.GlobalObject(
        title=u"``agx.core.interfaces.IHandler.__call__`` implementation",
        description=u"",
        required=False)

    order = schema.Int(
        title=u"Scope order",
        description=u"Execution order of the scope.",
        required=False)
