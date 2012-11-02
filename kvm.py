import os
import re
import random
import string
import time
import signal
from xml.dom.minidom import Document, Element, parseString
from xml.dom.minidom import _write_data
import unix.hosts as unix


################################################################################
########                    Hacks for XML fromatting                    ########
################################################################################
def writexml_document(self, writer, indent="", addindent="", newl=""):
    for node in self.childNodes:
        node.writexml(writer, indent, addindent, newl)


def writexml_element(self, writer, indent="", addindent="", newl=""):
    writer.write(newl + indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    onetextnode = False
    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        _write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        writer.write(">")
        lastnodetype=self.childNodes[0].nodeType
        for node in self.childNodes:
            if lastnodetype==node.TEXT_NODE:
                node.writexml(writer,"","","")
            else:
                node.writexml(writer, ("%s%s") % (indent,addindent), addindent, newl)
            lastnodetype=node.nodeType
        if lastnodetype==node.TEXT_NODE:
            writer.write("</%s>" % (self.tagName))
        else:
            writer.write("%s%s</%s>" % (newl,indent,self.tagName))
    else:
        writer.write("/>")

LANGUAGE = 'en_US.UTF-8'
RUNNING = 'running'
IDLE = 'idle'
PAUSED = 'paused'
SHUTDOWN = 'shutdown'
SHUTOFF = 'shut off'
CRASHED = 'crashed'
DYING = 'dying'

SIZE_REGEXP = re.compile('.*virtual size: [0-9.]*G \(([0-9]*) bytes\).*')
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

class TimeoutException(Exception):
    pass


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
            while self.state(vm) != SHUTOFF:
                pass
        except TimeoutException:
            if force:
                status, stdout,stderr = self.destroy(vm)
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
        return int(SIZE_REGEXP.search(stdout).group(1)) / 1024


    def img_create(self, img_path, format, size):
        return self.host.execute('qemu-img create -f %s %s %sG' % (
            format, img_path, size
        ))


    def img_convert(self, format, src_path, dst_path, delete=False):
        output = self.host.execute("qemu-img convert -O %s %s %s" % (
            format,
            src_path,
            dst_path
        ))
        if not delete or not output:
            return output

        return self.host.rm(src_path)


    def img_resize(self, path, new_size):
        return self.host.execute(
            "qemu-img resize %s %sG" % (path, new_size)
        )


    def img_load(self, path, nbd='/dev/nbd0'):
        if not self.host.loaded('nbd'):
            output = self.host.load('nbd')
            if not output[0]:
                return output

        output = self.host.execute("qemu-nbd -c %s %s" % (nbd, path))
        time.sleep(2)
        return output


    def img_unload(self, nbd='/dev/nbd0'):
        return self.host.execute("qemu-nbd -d %s" % nbd)


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

        disks = [
            {
                'path': self.__xml_attr(disk_node, 'source', 'file'),
                'type': self.__xml_attr(disk_node, 'driver', 'type'),
                'driver': self.__xml_attr(disk_node, 'target', 'bus'),
                'device': self.__xml_attr(disk_node, 'target', 'dev')
            }
            for disk_node in dom.getElementsByTagName('disk') \
            if disk_node.getAttribute('device') == 'disk'
        ]
        for index, disk in enumerate(disks):
            try:
                disks[index]['size'] = self.img_size(disk['path'])
            except OSError:
                disks[index]['size'] = 0

        interfaces = [
            {
                'mac': self.__xml_attr(int_node, 'mac', 'address'),
                'vlan': self.__xml_attr(int_node, 'source', 'bridge'),
                'interface': self.__xml_attr(int_node, 'target', 'dev'),
                'driver': self.__xml_attr(int_node, 'model', 'type')
            }
            for int_node in dom.getElementsByTagName('interface')
        ]

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


    def __node(self, name, attrs={}, text='', childs=[]):
        node = self.xml.createElement(name)
        for attr_name, attr_value in attrs.iteritems():
            node.setAttribute(attr_name, attr_value)
        if text:
            node.appendChild(self.xml.createTextNode(str(text)))
        if childs:
            for child_node in childs:
                node.appendChild(child_node)
        return node


    def _gen_devices_config(self, disks, interfaces):
        devices_nodes = [self.__node('emulator', text='/usr/bin/kvm')]

        # Add disks.
        devices_nodes.extend(
            (
                self.__node('disk', {'type': 'file', 'device': 'disk'}, childs=(
                    self.__node('driver', {'name': 'qemu', 'type': disk['format']}),
                    self.__node('source', {'file': disk['path']}),
                    self.__node('target', {'dev': disk['device'], 'bus': disk['driver']})
                ))
            ) for disk in disks
        )

        # Add interfaces.
        devices_nodes.extend(
            (
                self.__node('interface', {'type': 'bridge'}, childs=(
                    self.__node('mac', {'address': interface['mac']}),
                    self.__node('source', {'bridge': 'br%s' % interface['vlan']}),
                    self.__node('model', {'type': interface['driver']}),
                ))
                for interface in interfaces
            )
        )

        # Add other devices.
        devices_nodes.extend((
            self.__node('serial', {'type': 'pty'}, childs=(
                self.__node('target', {'port': '0'}),
            )),
            self.__node('console', {'type': 'pty'}, childs=(
                self.__node('target', {'port': '0'}),
            )),
            self.__node('input', {'type': 'mouse', 'bus': 'ps2'}),
            self.__node('graphics', {
                'type': 'vnc',
                'port': '-1',
                'autoport': 'yes',
                'keymap': 'fr'}
            ),
            self.__node('sound', {'model': 'es1370'}),
            self.__node('video', childs=(
                self.__node('model', {'type': 'cirrus', 'vram': '9216', 'heads': '1'}),
            )
        )))
        return devices_nodes


    def gen_conf(self, conf_file, params):
        # Hack for not printing xml version
        Document.writexml = writexml_document

        # Hack for XML output: text node on one line
        Element.writexml = writexml_element

        self.xml = Document()
#        memory = int(float(params['memory']) * 1024 * 1024)

        config = self.__node('domain', {'type': 'kvm'}, childs=(
            self.__node('name', text=params['name']),
            self.__node('uuid', text=params['uuid']),
            self.__node('memory', text=params['memory']),
            self.__node('currentMemory', text=params['memory']),
            self.__node('vcpu', text=params['cores']),
            self.__node('os', childs=(
                self.__node('type', {
                    'arch': 'x86_64',
#                    'machine': 'pc-0.11'
                }, 'hvm'),
                self.__node('boot', {'dev': 'hd'})
            )),
            self.__node('features', childs=(
                self.__node('acpi'),
                self.__node('apic'),
                self.__node('pae')
            )),
            self.__node('clock', {'offset': 'utc'}),
            self.__node('on_poweroff', text='destroy'),
            self.__node('on_reboot', text='restart'),
            self.__node('on_crash', text='restart'),
            self.__node('devices', childs=self._gen_devices_config(
                params['disks'],
                params['interfaces']
            ))
        ))

        return self.host.write(
            conf_file,
            '\n'.join(config.toprettyxml(indent='  ').split('\n')[1:])
        )


    def vms_conf(self):
        vms_conf = {}
        for vm in self.list():
            vms_conf.setdefault(vm, self.conf(vm))
        return vms_conf


    def mount(self, vgroot, lvroot, path):
        # Load root Volume Group.
        output = self.host.execute("vgchange -ay %s" % vgroot)
        if not output[0]:
            output[2] = "Unable to load root Volume Group: %s" % output[2]
            return output

        # Create mount point.
        if not self.host.exists(path):
            output = self.host.mkdir(path, True)
            if not output[0]:
                output[2] = "Unable to create mount point: %s" % output[2]
                return output

        # Mount root partition
        output = self.host.execute(
            "mount /dev/%s/%s %s" % (vgroot, lvroot, path)
        )
        if not output[0]:
            output[2] = "Unable to mount root partition: %s" % output[2]
            return output
        self.mounted = [path]

        # Read fstab
        try:
            lines = self.host.readlines(os.path.join(path, 'etc', 'fstab'))
        except OSError, os_err:
            return (False, "", "Unable to read fstab: %s" % output[2])

        for line in lines:
            if \
            line.find('/dev/mapper') == -1 or \
            line.find('/dev/mapper/%s-%s' % (vgroot, lvroot)) != -1 or \
            line.find('swap') != -1:
                continue
            dev, partition = line.split()[:2]
            mount_point = os.path.join(path, partition[1:])
            output = self.host.execute("mount %s %s" % (dev, mount_point))
            if not output[0]:
                output[2] = "Unable to mount '%s' partition: %s" % (partition, output[2])
                return output
            self.mounted.append(mount_point)
        return (True, "", "")


    def umount(self, vgroot):
        if not self.mounted:
            return (True, "", "Nothing was mounted")

        mounted = list(self.mounted)
        for mount in reversed(mounted):
            output = self.host.execute("umount %s" % mount)
            if not output[0]:
                output[2] = "Unable to umount '%s': %s" % (mount, output[2])
                return output
            self.mounted.remove(mount)

        output = self.host.execute("vgchange -an %s" % vgroot)
        if not output[0]:
            output[2] = "Unable to unload root Volume Group: %s" % output[2]
        return output
