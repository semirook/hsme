# coding: utf-8
import sys


PY = sys.version_info
PY3K = PY >= (3, 0, 0)


class ImportStringError(ImportError):
    import_name = None
    exception = None

    def __init__(self, import_name, exception):
        self.import_name = import_name
        self.exception = exception

        msg = (
            'import_string() failed for %r. Possible reasons are:\n\n'
            '- missing __init__.py in a package;\n'
            '- package or module path not included in sys.path;\n'
            '- duplicated package or module name taking precedence in '
            'sys.path;\n'
            '- missing module, class, function or variable;\n\n'
            'Debugged import:\n\n%s\n\n'
            'Original exception:\n\n%s: %s')

        name = ''
        tracked = []
        for part in import_name.replace(':', '.').split('.'):
            name += (name and '.') + part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, '__file__', None)))
            else:
                track = ['- %r found in %r.' % (n, i) for n, i in tracked]
                track.append('- %r not found.' % name)
                msg = msg % (
                    import_name,
                    '\n'.join(track),
                    exception.__class__.__name__,
                    str(exception),
                )
                break

        ImportError.__init__(self, msg)

    def __repr__(self):
        return '<%s(%r, %r)>' % (
            self.__class__.__name__,
            self.import_name,
            self.exception,
        )


def import_string(import_name, silent=False):
    import_name = str(import_name)
    try:
        if ':' in import_name:
            module, obj = import_name.split(':', 1)
        elif '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
        else:
            return __import__(import_name)
        if not PY3K and isinstance(obj, unicode):
            obj = obj.encode('utf-8')
        try:
            return getattr(__import__(module, None, None, [obj]), obj)
        except (ImportError, AttributeError):
            modname = module + '.' + obj
            __import__(modname)
            return sys.modules[modname]
    except ImportError as e:
        if not silent:
            raise ImportStringError(import_name, e)
