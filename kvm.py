"""This module allow to manage KVM hosts."""

import os
import re
import json
import random
import string
import weakref
import unix
import lxml.etree as etree
from collections import OrderedDict

import sys
_SELF = sys.modules[__name__]
_BUILTINS = sys.modules['builtins'
                        if sys.version_info.major == 3
                        else '__builtin__']


# Controls.
_CONTROLS = {'parse': False, 'ignore_opts': []}
unix._CONTROLS.update(_CONTROLS)

# Characters in generating strings.
_CHOICES = string.ascii_letters[:6] + string.digits

_ITEM_RE = re.compile('^.IX (?P<type>\w+) "(?P<value>.*)"$')

__MAPFILE = os.path.join(os.path.dirname(__file__), 'kvm.json')
_MAPPING = json.loads(''.join([line
                               for line in open(__MAPFILE).readlines()
                               if not line.startswith('#')]))

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
    def parse(tag_name, conf):
        tag = etree.Element(tag_name)
        for elt, value in conf.items():
            if elt.startswith('@'):
                tag.attrib[elt[1:]] = str(value)
            elif elt == '#text':
                tag.text = str(value)
            elif isinstance(value, dict):
                tag.append(parse(elt, value))
            elif isinstance(value, list):
                for child in value:
                    tag.append(parse(elt, child))
            elif isinstance(value, bool):
                tag.append(etree.Element(elt))
                continue
            else:
                child = etree.Element(elt)
                child.text = value
                tag.append(child)
        return tag
    return etree.tostring(parse(tag_name, conf), pretty_print=True).decode()


def _str_to_dict(lines):
    def format_key(key):
        return (key.strip().lower()
                   .replace(' ', '_').replace('(', '').replace(')', ''))

    return {format_key(key): _convert((value or '').strip())
            for line in lines if line
            for key, value in [line.split(':')]}


def _stats(lines, ignore=False):
    return {elts[1 if ignore else 0]: elts[2 if ignore else 1]
            for line in lines if line
            for elts in [line.split()]}


def _list(lines):
    params = [param.lower() for param in re.split('\s+', lines[0])][1:]
    return [dict(zip(params, re.split('\s+', line)[1:])) for line in lines[2:]]


def __add_method(obj, method, conf):
    cmd = conf.get('cmd', method)
    ignore_opts = conf.pop('disable', [])
    def str_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True, ignore_opts=ignore_opts):
            result = self._host.virsh(cmd, *args, **kwargs)[0]
            if 'convert' in conf:
                try:
                    return getattr(_BUILTINS, conf['convert'])(result)
                except ValueError:
                    return -1 if conf['convert'] == 'int' else result
            return result

    def dict_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True, ignore_opts=ignore_opts):
            return _str_to_dict(self._host.virsh(cmd, *args, **kwargs))

    def stats_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True, ignore_opts=ignore_opts):

            return _stats(self._host.virsh(cmd, *args, **kwargs),
                          conf.get('ignore', False))

    def list_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True, ignore_opts=ignore_opts):
            return _list(self._host.virsh(cmd, *args, **kwargs))

    def tune_method(self, *args, **kwargs):
        ignore_opts = ('config', 'live', 'current')
        if (not kwargs
          or (len(kwargs) == 1 and any(opt in kwargs for opt in ignore_opts))):
            return dict_method(self, *args, **kwargs)
        else:
            return none_method(self, *args, **kwargs)

    def none_method(self, *args, **kwargs):
        return self._host.virsh(cmd, *args, **kwargs)

    def xml_method(self, *args, **kwargs):
        with self._host.set_controls(parse=True, ignore_opts=ignore_opts):
            xml = '\n'.join(self._host.virsh(cmd, *args, **kwargs))
        return from_xml(etree.fromstring(xml), conf.get('lists', []))[conf['key']]

    setattr(obj, method.replace('-', '_'), locals()['%s_method' % conf['type']])


def _convert(value):
    value = value.strip()
    if value.isdigit():
        return int(value)
    for val, map_val in (('yes', True), ('no', False)):
        if value == val:
            return map_val
    return value


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
            if self._ignore_opts:
                for opt in self._ignore_opts:
                    kwargs.update({opt: False})
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


        def list_networks(self, **kwargs):
            with self.set_controls(parse=True):
                stdout = self.virsh('net-list', **kwargs)
                networks = {}
                for line in stdout[2:]:
                    line = line.split()
                    name, state, autostart = line[:3]
                    net = dict(state=state, autostart=_convert(autostart))
                    if len(line) == 4:
                        net.update(persistent=_convert(line[3]))
                    networks.setdefault(name, net)
            return networks


        @property
        def image(self):
            return _Image(weakref.ref(self)())



    for property_name, property_methods in _MAPPING.items():
        property_obj = type('_%s' % property_name.capitalize(),
                            (object,),
                            dict(__init__=__init))

        for method_name, method_conf in property_methods.items():
            __add_method(property_obj, method_name, method_conf)
        #    getattr(Hypervisor, method['name']).__doc__ = '\n'.join(method['doc'])

        for method_name in dir(_SELF):
            if method_name.startswith('__%s' % property_name):
                method = method_name.replace('__%s_' % property_name, '')
                setattr(property_obj, method, getattr(_SELF, method_name))
        setattr(Hypervisor, property_name, property(property_obj))


    return Hypervisor()


def __init(self, host):
    self._host = host


def __domain_time(self, domain, **kwargs):
    kwargs.pop('pretty', None)
    if not kwargs:
        from datetime import datetime
        with self._host.set_controls(parse=True):
            time = self._host.virsh('domtime', domain, **kwargs)[0]
            return datetime.fromtimestamp(int(time.split(':')[1]))
    else:
        return self._host.virsh('domtime', domain, **kwargs)


def __domain_cpustats(self, domain, **kwargs):
    with self._host.set_controls(parse=True):
        lines = self._host.virsh('cpu-stats', domain, **kwargs)
        stats = {}
        cur_cpu = ''
        for line in lines:
            if not line.startswith('\t'):
                cur_cpu = line[:-1].lower()
                stats.setdefault(cur_cpu, {})
            else:
                param, value, unit = line[1:].split()
                stats[cur_cpu][param] = '%s %s' % (value, unit)
        return stats


def __domain_stop(self, domain, timeout=30, force=False):
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
            print(self.state(domain), SHUTOFF)
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
