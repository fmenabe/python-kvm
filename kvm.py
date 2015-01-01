"""This module allow to manage KVM hosts."""

import os
import re
import random
import string
import weakref
import unix
from lxml import etree

import sys
SELF = sys.modules[__name__]


# Controls.
CONTROLS = {'parse': False}
unix.CONTROLS.update(CONTROLS)

# Characters in generating strings.
_CHOICES = string.ascii_letters[:6] + string.digits

MAPPING = {'hypervisor': {'version': {'type': 'dict'},
                          'sysinfo': {'type': 'dict'},
                          'nodeinfo': {'type': 'dict'},
                          'nodecpumap': {'type': 'dict'},
                          'nodecpustats': {'type': 'dict'},
                          'nodememstats': {'type': 'dict'},
                          'nodesuspend': {'type': 'none'},
                          'node_memory_tune': {'type': 'none'},
                          'capabilities': {'type': 'xml',
                                           'key': 'capabilities'},
                          'domcapabilities': {'type': 'xml',
                                              'key': 'domainCapabilities'},
                          'freecell': {'type': 'dict'},
                          'freepages': {'type': 'dict'},
                          'allocpages': {'type': 'none'}}}


#
# Functions for generating datas.
#
def gen_uuid():
    """Generate a random uuid."""
    return '-'.join((''.join([random.choice(_CHOICES) for _ in range(0, 8)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 4)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 4)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 4)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 12)])))


def gen_mac():
    """Generate a random mac address."""
    return ':'.join(('54', '52', '00',
                     ''.join([random.choice(_CHOICES) for _ in range(0, 2)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 2)]),
                     ''.join([random.choice(_CHOICES) for _ in range(0, 2)])))


def _xml_to_dict(elt):
    """Recursive function that transform an XML element to a dictionnary.
    **elt** must be of type ``lxml.etree.Element``."""
    tag = elt.tag
    attrs = elt.items()
    text = elt.text.strip() if elt.text else None
    childs = elt.getchildren()

    if not attrs and not childs and not text:
        return {tag: True}
    elif not attrs and not childs and text:
        return {tag: text}
    elif attrs and not childs:
        child = {'@%s' % attr: value for attr, value in attrs}
        if text:
            child['#text'] = text
        return {tag: child}
    elif childs:
        elts = {'@%s' % attr: value for attr, value in attrs} if attrs else {}
        for child in childs:
            child = _xml_to_dict(child)
            child_tag = list(child.keys())[0]
            if child_tag  in elts:
                if not isinstance(elts[child_tag], list):
                    elts[child_tag] = [elts[child_tag]]
                elts[child_tag].append(child[child_tag])
            else:
                elts.update(child)
        return {tag: elts}


def __str_to_dict(string):
    def format_key(key):
        return (key.strip().lower()
                   .replace(' ', '_').replace('(', '').replace(')', ''))
    return {format_key(key): (value or '').strip()
            for line in string if line
            for key, value in [line.split(':')]}


def __add_method(obj, method, conf):
    def dict_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            return __str_to_dict(self._host.virsh(method, *args, **kwargs))

    def none_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            stdout = self._host.virsh(method, *args, **kwargs)

    def xml_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            xml = '\n'.join(self._host.virsh(method, *args, **kwargs))
        return _xml_to_dict(etree.fromstring(xml))[conf['key']]

    setattr(obj, method, locals()['%s_method' % conf['type']])


#
# Exceptions
#
class KvmError(Exception):
    """Main exception for this module."""
    pass


#
## Classes.
#
def Hypervisor(host):
    unix.isvalid(host)

    class Hypervisor(host.__class__):
        """This object represent an Hypervisor. **host** must be an object of
        type ``unix.Local`` or ``unix.Remote`` (or an object inheriting from
        them).
        """
        def __init__(self):
            host.__class__.__init__(self)
            self.__dict__.update(host.__dict__)
            for control, value in iteritems(CONTROLS):
                setattr(self, '_%s' % control, value)


        def virsh(self, command, *args, **kwargs):
            """Wrap the execution of the virsh command. It set a control for
            putting options after the virsh **command**. If **parse** control
            is activated, the value of ``stdout`` is returned or **KvmError**
            exception is raised.
            """
            with self.set_controls(options_place='after', decode='utf-8'):
                status, stdout, stderr = self.execute('virsh',
                                                      command,
                                                      *args,
                                                      **kwargs)
                if not self._parse:
                    return status, stdout, stderr
                elif not status:
                    raise KvmError(stderr)
                else:
                    return stdout.splitlines()[:-1]


        @property
        def hypervisor(self):
            return _Hypervisor(weakref.ref(self)())

    return Hypervisor()


class _Hypervisor(object):
    def __init__(self, host):
        self._host = host

for mname, mconf in MAPPING['hypervisor'].items():
    __add_method(_Hypervisor, mname, mconf)
