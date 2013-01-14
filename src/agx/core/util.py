import agx.core


def writesourcepath(source, elem):
    setattr(elem, '_AGX_Target_sourcepath', source.path)


def readsourcepath(elem):
    return getattr(elem, '_AGX_Target_sourcepath', [])


def write_source_to_target_mapping(source, target):
    tok = agx.core.token('sourcetotargetuuidmapping', True, uuids={})
    tok.uuids[source.uuid] = target.uuid


def read_target_node(source, target):
    tok = agx.core.token('sourcetotargetuuidmapping', False)
    target_uuid = tok.uuids.get(source.uuid)
    if not target_uuid:
        return None
    return target.node(target_uuid)


def normalizetext(text):
    """Normalize a piece of text.
    
    All whitespaces are stripped down to the count of 1, all lines returned
    have a max length of 60 characters.
    """
    words = text.split(' ')
    words = [word for word in words if word]
    lines = list()
    charcount = 0
    start = 0
    end = 0
    for word in words:
        charcount = charcount + len(word) + 1
        if charcount >= 60:
            lines.append(' '.join(words[start:end]))
            start = end
            charcount = 0
        end += 1
    if end <= len(words):
        lines.append(' '.join(words[start:]))
    return '\n'.join(lines)


def dotted_path(node):
    """Returns the dotted python path of an entity.
    """
    return '.'.join(node.path[1:])
