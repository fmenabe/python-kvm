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

RUNNING = 'running'
IDLE = 'idle'
PAUSED = 'paused'
SHUTDOWN = 'shutdown'
SHUTOFF = 'shut off'
CRASHED = 'crashed'
DYING = 'dying'
SUSPENDED = 'pmsuspended'

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
                          'allocpages': {'type': 'none'}},
           'domain': {'autostart': {'type': 'none'},
                      'inject-nmi': {'type': 'none'},
                      'desc': {'type': 'dict'},
                      'destroy': {'type': 'none'},
                      'domblkinfo': {'type': 'dict'},
                      'domdisplay': {'type': 'str'},
                      'dominfo': {'type': 'dict'},
                      'domuuid': {'type': 'str'},
                      'domid': {'type': 'str'},
                      'domname': {'type': 'str'},
                      'domstate': {'type': 'str'},
                      'domcontrol': {'type': 'str'},
                      'dumpxml': {'type': 'xml',
                                  'key': 'domain'},
                      'reboot': {'type': 'none'},
                      'reset': {'type': 'none'},
                      'screenshot': {'type': 'none'},
                      'shutdown': {'type': 'none'},
                      'start': {'type': 'none'},
                      'suspend': {'type': 'none'},
                      'resume': {'type': 'none'},
                      'ttyconsole': {'type': 'str'},
                      'undefine': {'type': 'none'},
           }}


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
    def str_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            return self._host.virsh(method, *args, **kwargs)[0]

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


class TimeoutException(Exception):
    """Exception raise when a timeout is exceeded."""
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
            for control, value in CONTROLS.items():
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
                    stdout = stdout.splitlines()
                    return stdout[:-1] if not stdout[-1] else stdout


        @property
        def hypervisor(self):
            return _Hypervisor(weakref.ref(self)())


        @property
        def domain(self):
            return _Domain(weakref.ref(self)())


        def list_domains(self, **kwargs):
            """List domains. **kwargs** parameters can be:
                * *all*: list all domains
                * *inactive*: list only inactive domains
                * *persisten*: include persistent domains
                * *transient*: include transient domains
                * *autostart*: list autostarting domains
                * *no_autostart*: list not autostarting domains
                * *with_snapshot*: list domains having snapshots
                * *without_snapshort*: list domains not having snapshots
                * *managed_save*:  domains that have managed save state (only
                                   possible if they are in the shut off state,
                                   so you need to specify *inactive* or *all*
                                   to actually list them) will instead show as
                                   saved
                * *with_managed_save*: list domains having a managed save image
                * *without_managed_save*: list domains not having a managed save
                                          image
                * *states*: filter on given states (automatically set *all*
                            option)
            """
            virsh_kwargs = {'table': True}
            states = kwargs.pop('states', [])
            if states:
                kwargs['all'] = True

            # Add virsh options for kwargs.
            for arg, value in kwargs.items():
                if not value:
                    continue
                virsh_kwargs.update({arg: True})

            # Get domains (filtered on state).
            with self.set_controls(parse=True):
                domains = {name: {'id': domid,
                                  'state': ' '.join(state)}
                           for line in self.virsh('list', **virsh_kwargs)[2:]
                           for domid, name, *state in [line.strip().split()]
                           if not states or ' '.join(state) in states}

            return domains

    return Hypervisor()


class _Hypervisor(object):
    def __init__(self, host):
        self._host = host

for mname, mconf in MAPPING['hypervisor'].items():
    __add_method(_Hypervisor, mname, mconf)


class _Domain(object):
    def __init__(self, host):
        self._host = host


    def create(self, conf, *kwargs):
        pass


    def define(self, conf):
        pass


    def stop(self, domain, timeout=30, force=False):
        import signal, time

        def timeout_handler(signum, frame):
            raise TimeoutException()

        self.shutdown(domain)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            while self.domstate(domain) != SHUTOFF:
                time.sleep(1)
        except TimeoutException:
            if force:
                self.destroy(domain)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)

for mname, mconf in MAPPING['domain'].items():
    __add_method(_Domain, mname, mconf)
