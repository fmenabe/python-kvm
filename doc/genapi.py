import sys
sys.path.append('..')
import unix
import kvm
import inspect
from inspect import cleandoc
from textwrap import dedent
from jinja2 import Environment, PackageLoader

METHODS = ('gen_uuid', 'gen_mac', '_xml_to_dict')
OBJ_METHODS = ('virsh',)
CHILDS = ('generic',)
PREFIX = 'hypervisor'
INDENT = 10

def params(obj, method, prefix=''):
    obj = getattr(obj, method)

    # Get method signature.
    signature = '%s%s%s' % ('%s.' % prefix if prefix else '',
                            method,
                            inspect.signature(obj))

    # Format docstring.
    doc = cleandoc(obj.__doc__ or '*NOT DOCUMENTED*')
    return {'signature': signature, 'doc': doc}


def main():
    env = Environment(loader=PackageLoader('kvm', 'doc/templates'))
    docstrings = {'module': kvm.__doc__ or '*NOT DOCUMENTED*'}

    # Add methods.
    docstrings.update(**{method: params(kvm, method) for method in METHODS})

    # Add exceptions.
    docstrings.update(KvmError=cleandoc(getattr(kvm, 'KvmError').__doc__))

    hypervisor = kvm.Hypervisor(unix.Local())

    # Add Hypervisor methods.
    hypervisor_docstrings = {'doc': cleandoc(hypervisor.__doc__)}
    hypervisor_docstrings.update(**{method: params(hypervisor, method, PREFIX)
                                    for method in OBJ_METHODS})

    # Add childs objects.
    for child in CHILDS:
        prefix = '%s.%s' % (PREFIX, 'generic')

        child_obj = getattr(kvm, '_%s' % child.capitalize())
        for method in dir(child_obj):
            if method.startswith('_'):
                continue
            (hypervisor_docstrings.setdefault('childs', {})
                                  .setdefault(child, [])
                                  .append(params(child_obj, method, prefix)))

    docstrings.update(hypervisor = hypervisor_docstrings)

    api = env.get_template('api.rst')
    print(api.render(**docstrings))


if __name__ == '__main__':
    main()
