"""This module allow to manage KVM hosts."""

import os
import re
import random
import string
import weakref
import unix
import lxml.etree as etree
from collections import OrderedDict

import sys
SELF = sys.modules[__name__]


# Controls.
_CONTROLS = {'parse': False}
unix._CONTROLS.update(_CONTROLS)

# Characters in generating strings.
_CHOICES = string.ascii_letters[:6] + string.digits

_ITEM_RE = re.compile('^.IX (?P<type>\w+) "(?P<value>.*)"$')

_MAPPING = {'hypervisor': {'version': {'type': 'dict'},
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
                       'create': {'type': 'none'},
                       'define': {'type': 'none'},
                       'desc': {'type': 'dict'},
                       'destroy': {'type': 'none'},
                       'blkstat': {'cmd': 'domblkstat',
                                   'type': 'stats',
                                   'ignore': True,
                                   'disable': ['human']},
                       'ifstat': {'cmd': 'domifstat',
                                  'type': 'stats',
                                  'ignore': True},
                       'if_setlink': {'cmd': 'domif-setlink', 'type': 'none'},
                       'if_getlink': {'cmd': 'domif-getlink', 'type': 'none'},
                       'iftune': {'type': 'none'},
                       'memstat': {'cmd': 'dommemstat', 'type': 'stats'},
                       'blkinfo': {'cmd': 'domblkinfo', 'type': 'dict'},
                       'blklist': {'cmd': 'domblklist', 'type': 'list'},
                       'display': {'cmd': 'domdisplay', 'type': 'str'},
                       'info': {'cmd': 'dominfo', 'type': 'dict'},
                       'uuid': {'cmd': 'domuuid', 'type': 'str'},
                       'id': {'cmd': 'domid', 'type': 'str'},
                       'name': {'cmd': 'domname', 'type': 'str'},
                       'state': {'cmd': 'domstate', 'type': 'str'},
                       'control': {'cmd': 'domcontrol', 'type': 'str'},
                       'conf': {'cmd': 'dumpxml',
                                'type': 'xml',
                                'key': 'domain',
                                'lists': ['disk', 'interface']},
                       'reboot': {'type': 'none'},
                       'reset': {'type': 'none'},
                       'screenshot': {'type': 'none'},
                       'shutdown': {'type': 'none'},
                       'start': {'type': 'none'},
                       'suspend': {'type': 'none'},
                       'resume': {'type': 'none'},
                       'ttyconsole': {'type': 'str'},
                       'undefine': {'type': 'none'},
                       'attach-disk': {'type': 'none'},


RUNNING = 'running'
IDLE = 'idle'
PAUSED = 'paused'
SHUTDOWN = 'shutdown'
SHUTOFF = 'shut off'
CRASHED = 'crashed'
DYING = 'dying'
SUSPENDED = 'pmsuspended'


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


def from_xml(elt, force_lists=[]):
    """Recursive function that transform an XML element to a dictionnary.
    **elt** must be of type ``lxml.etree.Element``."""
    tag = elt.tag
    attrs = elt.items()
    text = elt.text.strip() if elt.text else None
    childs = elt.getchildren()

    if not attrs and not childs and not text:
        value = True
    elif not attrs and not childs and text:
        value = text
    elif attrs and not childs:
        child = {'@%s' % attr: value for attr, value in attrs}
        if text:
            child['#text'] = text
        value = child
    elif childs:
        elts = (OrderedDict(('@%s' % attr, value) for attr, value in attrs)
                if attrs else OrderedDict())
        for child in childs:
            child = from_xml(child, force_lists)
            child_tag = list(child.keys())[0]
            if child_tag in force_lists:
                elts[child_tag] = []
            if child_tag  in elts:
                if not isinstance(elts[child_tag], list):
                    elts[child_tag] = [elts[child_tag]]
                elts[child_tag].append(child[child_tag])
            else:
                elts.update(child)
        value = elts

    result = OrderedDict()
    result[tag] = value
    return result


def to_xml(tag_name, conf):
    tag = etree.Element(tag_name)
    for elt, value in conf.items():
        if elt.startswith('@'):
            tag.attrib[elt[1:]] = str(value)
        elif elt == '#text':
            tag.text = str(value)
        elif isinstance(value, dict):
            tag.append(to_xml(elt, value))
        elif isinstance(value, list):
            for child in value:
                tag.append(to_xml(elt, child))
        elif isinstance(value, bool):
            tag.append(etree.Element(elt))
            continue
        else:
            child = etree.Element(elt)
            child.text = value
            tag.append(child)
    return tag


def _str_to_dict(lines):
    def format_key(key):
        return (key.strip().lower()
                   .replace(' ', '_').replace('(', '').replace(')', ''))
    return {format_key(key): (value or '').strip()
            for line in lines if line
            for key, value in [line.split(':')]}


def _stats(lines, ignore=False):
    return {elts[1 if ignore else 0]: elts[2 if ignore else 1]
            for line in lines if line
            for elts in [line.split()]}


def _list(lines):
    params = [param.lower() for param in re.split('\s+', lines[0])]
    return [dict(zip(params, re.split('\s+', line))) for line in lines[2:]]


def __add_method(obj, method, conf):
    cmd = conf.get('cmd', method)
    def str_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            return self._host.virsh(cmd, *args, **kwargs)[0]

    def dict_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            return _str_to_dict(self._host.virsh(cmd, *args, **kwargs))

    def stats_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            for opt in conf.get('disable', []):
                kwargs[opt] = False
            return _stats(self._host.virsh(cmd, *args, **kwargs),
                          conf.get('ignore', False))

    def list_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            return _list(self._host.virsh(cmd, *args, **kwargs))

    def none_method(self, *args, **kwargs):
        return self._host.virsh(method, *args, **kwargs)

    def xml_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True):
            xml = '\n'.join(self._host.virsh(cmd, *args, **kwargs))
        return from_xml(etree.fromstring(xml), conf.get('lists', []))[conf['key']]

    setattr(obj, method.replace('-', '_'), locals()['%s_method' % conf['type']])


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

    try:
        host.which('virsh')
    except unix.UnixError:
        raise KvmError("unable to find 'virsh' command, is this a KVM host?")

    class Hypervisor(host.__class__):
        """This object represent an Hypervisor. **host** must be an object of
        type ``unix.Local`` or ``unix.Remote`` (or an object inheriting from
        them).
        """
        def __init__(self):
            host.__class__.__init__(self)
            self.__dict__.update(host.__dict__)
            for control, value in _CONTROLS.items():
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
                # Clean stdout and stderr.
                if stdout:
                    stdout = stdout.rstrip('\n')
                if stderr:
                    stderr = stderr.rstrip('\n')

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
            """List domains. **kwargs** can contains any option supported by the
            virsh command. It can also contains a **state** argument which is a
            list of states for filtering (*all* option is automatically set).
            For compatibility the options ``--table``, ``--name`` and ``--uuid``
            have been disabled.

            Virsh options are (some option may not work according your version):
                * *all*: list all domains
                * *inactive*: list only inactive domains
                * *persistent*: include persistent domains
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
                * *without_managed_save*: list domains not having a managed
                                          save image
            """
            # Remove incompatible options between virsh versions.
            kwargs.pop('name', None)
            kwargs.pop('uuid', None)

            # Get states argument (which is not an option of the virsh command).
            states = kwargs.pop('states', [])
            if states:
                kwargs['all'] = True

            # Add virsh options for kwargs.
            virsh_opts = {arg: value for arg, value in kwargs.items() if value}

            # Get domains (filtered on state).
            domains = {}
            with self.set_controls(parse=True):
                stdout = self.virsh('list', **virsh_opts)

                for line in stdout[2:]:
                    line = line.split()
                    (domid, name, state), params = line[:3], line[3:]
                    # Manage state in two words.
                    if state == 'shut':
                        state += ' %s' % params.pop(0)
                    domain = {'id': int(domid) if domid != '-' else -1,
                              'state': state}
                    if 'title' in kwargs:
                        domain['title'] = ' '.join(params) if params else ''
                    domains[name] = domain

            return domains


        @property
        def image(self):
            return _Image(weakref.ref(self)())


    return Hypervisor()


class _Hypervisor(object):
    def __init__(self, host):
        self._host = host

for mname, mconf in _MAPPING['hypervisor'].items():
    __add_method(_Hypervisor, mname, mconf)


class _Domain(object):
    def __init__(self, host):
        self._host = host


    def gen_conf(self, conf):
        return etree.tostring(to_xml('domain', conf), pretty_print=True)




    def stop(self, domain, timeout=30, force=False):
        import signal, time

        def timeout_handler(signum, frame):
            raise TimeoutException()

        # Check guest exists.
        if domain not in self._host.list_domains(all=True):
            return [False, '', 'Domain not found']

        self.shutdown(domain)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            while self.state(domain) != SHUTOFF:
                time.sleep(1)
        except TimeoutException:
            if force:
                status, stdout, stderr = self.destroy(domain)
                if status:
                    stderr = 'VM has been destroyed after %ss' % timeout
                return (status, stdout, stderr)
            else:
                return (False, '', 'VM not stopped after %ss' % timeout)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)
        return [True, '', '']


class _Image(object):
    def __init__(self, host):
        self._host = host


    def check(self, path, **kwargs):
        return self._host.execute('qemu-img check', path, **kwargs)


    def create(self, path, size, **kwargs):
        return self._host.execute('qemu-img create', path, size, **kwargs)


    def commit(self, path, **kwargs):
        return self._host.execute('qemu-img commit', path, **kwargs)


    def compare(self, *paths, **kwargs):
        return self._host.execute('qemu-img compare', *paths, **kwargs)


    def convert(self, src_path, dst_path, **kwargs):
        with self._host.set_controls(options_place='after'):
            return self._host.execute('qemu-img convert', src_path, dst_path, **kwargs)


    def info(self, path, **kwargs):
        status, stdout, stderr = self._host.execute('qemu-img info', path, **kwargs)
        if not status:
            raise OSError(stderr)
        return _str_to_dict(stdout.splitlines())


    def map(self, path, **kwargs):
        return self._host.execute('qemu-img map', path, **kwargs)


    def snapshot(self, path, **kwargs):
        return self._host.execute('qemu-img snapshot', path, **kwargs)


    def rebase(self, path, **kwargs):
        return self._host.execute('qemu-img rebase', path, **kwargs)


    def resize(self, path, size):
        return self._host.execute('qemu-img resize', path, size)


    def amend(self, path, **kwargs):
        return self._host.execute('qemu-img amend', path, **kwargs)


    def load(self, path, device='nbd0', **kwargs):
        kwargs['c'] = '/dev/%s' % device
        kwargs['d'] = False
        return self._host.execute('qemu-nbd', path, **kwargs)


    def unload(self, device='nbd0', **kwargs):
        kwargs['c'] = False
        kwargs['d'] = '/dev/%s' % device
        return self._host.execute('qemu-nbd', **kwargs)


for mname, mconf in _MAPPING['domain'].items():
    __add_method(_Domain, mname, mconf)
