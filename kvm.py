import os
import re
import random
import string
from xml.dom.minidom import Document, Element, parseString
import unix.hosts as unix

LANGUAGE = 'en_US.UTF-8'
RUNNING = 'running'
IDLE = 'idle'
PAUSED = 'paused'
SHUTDOWN = 'shutdown'
SHUTOFF = 'shut off'
CRASHED = 'crashed'
DYING = 'dying'

SIZE_REGEXP = re.compile('.*virtual size: [0-9]*G \(([0-9]*) bytes\).*')
UNKNOWN_CMD_REGEXP = re.compile("error: unknown command: '(.*)'")
BAD_OPTION_REGEXP = re.compile("error: command '(.*)' doesn't support option '(.*)'")


CHOICES = string.letters[:6] + string.digits
def gen_uuid():
    return '-'.join((
        ''.join([random.choice(CHOICES) for i in xrange(0, 8)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 12)]),
    ))


def gen_mac():
    return ':'.join((
        '54', '52', '00',
        ''.join([random.choice(CHOICES) for i in xrange(0, 2)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 2)]),
        ''.join([random.choice(CHOICES) for i in xrange(0, 2)])
    ))


class KVMError(Exception):
    pass


class TimeoutExecption(Exception):
    pass


class KVM(object):
    def __init__(self, host, username='root', password='', timeout=10, ipv6=False):
        self.host = unix.RemoteHost()
        self.host.connect(host, username, password, timeout, ipv6)


    def virsh(self, command, args):
        self.host._connected()

        virsh_cmd = ' '.join((
            'LANGUAGE=%s' % LANGUAGE,
            'virsh',
            command,
            args,
        ))
        status, stdout, stderr = self.host.execute(virsh_cmd)
        if not status \
        and (UNKNOWN_CMD_REGEXP.match(stderr) or BAD_OPTION_REGEXP.match(stderr)):
            raise KVMError('%s: %s' % (virsh_cmd, stderr))
        return (status, stdout, stderr)


    def list(self):
        return [
            vm.split()[1] \
            for vm in self.virsh('list', '--all')[1].split('\n')[2:-2]
        ]


    def exists(self, vm):
        return True if vm in self.list() else False


    def state(self, vm):
        if not self.exists(vm):
            return (False, '', 'VM not exists')

        return self.virsh('domstate', vm)[1].split('\n')[0]


    def start(self, vm):
        return self.virsh('start', vm)


    def stop(self, vm, timeout=30, force=False):
        output = self.virsh('shutdown', vm)
        if not output[0]:
            return output

        def timeout_handler(signum, frame):
            raise TimeoutException()
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            while self.state() != SHUTOFF:
                pass
        except TimeoutException:
            if force:
                status, stdout,stderr = self.virsh('destroy')
                stderr = 'VM has been destroy after %ss' % timeout
                return (status, stdout, stderr)
            else:
                return (False, '', 'VM not stopping after %ss' % timeout)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)

        return output


    def destroy(self, vm):
        return self.virsh('destroy', vm)


    def define(self, conf_file):
        return self.virsh('define', conf_file)


    def undefine(self, vm, del_img=False):
        return self.virsh('undefine', vm)


    def migrate(self, vm, dst):
        return self.virsh('migrate', ' '.join(
            "--connect",
            "qemu:///system",
            "--live",
            "--persistent",
            "--copy-storage-all",
            "%s qemu+ssh://%s/system" % (vm, dst)
        ))

    def img_size(self, img_path):
        if not self.host.exists(img_path):
            raise OSError("file '%s' not exists" % img_path)
        stdout = self.host.execute('qemu-img info %s' % img_path)[1]
        return int(SIZE_REGEXP.search(stdout).group(1))

    def img_create(self, img_path, format, size):
        return self.host.execute('qemu-img create -f %s %s %sG' % (
            format, img_path, size
        ))


    def img_convert(self, img_path, format, options):
        pass


    def __xml_value(self, elt, tag):
        return elt.getElementsByTagName(tag)[0].childNodes[0].data


    def __xml_attr(self, elt, tag, attr):
        try:
            return elt.getElementsByTagName(tag)[0].getAttribute(attr)
        except IndexError:
            return ''


    def conf(self, vm):
        if not self.exists(vm):
            raise KVMError("VM '%s' not exists" % vm)
        xml_conf = self.virsh('dumpxml', vm)[1]
        dom = parseString(xml_conf)

        disks = dict((
            (
                self.__xml_attr(disk_node, 'source', 'file'),
                {
                    'type': self.__xml_attr(disk_node, 'driver', 'type'),
                    'driver': self.__xml_attr(disk_node, 'target', 'bus'),
                    'device': self.__xml_attr(disk_node, 'target', 'dev')
                }
            ) \
            for disk_node in dom.getElementsByTagName('disk') \
            if disk_node.getAttribute('device') == 'disk'
        ))
        for disk_path in disks:
            disks[disk_path].setdefault('size', self.img_size(disk_path))

        interfaces = dict((
            (
                self.__xml_attr(int_node, 'mac', 'address'),
                {
                    'vlan': self.__xml_attr(int_node, 'source', 'bridge'),
                    'interface': self.__xml_attr(int_node, 'target', 'dev'),
                    'driver': self.__xml_attr(int_node, 'model', 'type')
                }
            ) for int_node in dom.getElementsByTagName('interface')
        ))


        return {
            'pc': self.__xml_attr(dom.getElementsByTagName('os')[0], 'type', 'machine'),
            'name': self.__xml_value(dom, 'name'),
            'uuid': self.__xml_value(dom, 'uuid'),
            'memory': int(self.__xml_value(dom, 'currentMemory')),
            'memory_max': int(self.__xml_value(dom, 'memory')),
            'cores': int(self.__xml_value(dom, 'vcpu')),
            'disks': disks,
            'interfaces': interfaces
        }


    def gen_conf(self, conf_file, vm, cores=2, mem=2, **params):
        pass


    def parse_conf(self, conf_file):
        pass
