Config
======

Check if configuration loader was registered properly::

    >>> from zope.component import getUtility
    >>> from agx.core.interfaces import IConfLoader
    >>> loader = getUtility(IConfLoader)
    >>> loader
    <...ConfLoader object at ...>
