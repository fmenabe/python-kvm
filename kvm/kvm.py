import os
import time
import re
import signal
from hosts import Host
#from unix.remote import RemoteHost
from xml.dom.minidom import Document, Element, parseString
import random
import string
from utils import writexml_document, writexml_element




CHOICES = string.letters[:6] + string.digits
"""Characters used when generating UUID and mac address (ie: [0-9a-f])."""

UNKNOWN_CMD_REGEXP = re.compile("error: unknown command: '(.*)'")
"""Regular expression for matching bad I{virsh} command."""
BAD_OPTION_REGEXP = re.compile("error: command '(.*)' doesn't support option '(.*)'")
"""Regular expression for matching bad I{virsh} option."""


class TimeoutException(Exception):
    """Exception raised when a defined timeout occur."""
    pass


class KVMError(Exception):
    """Exception raised if a given Host has not 'kvm' module loaded."""
    pass


class VirshError(Exception):
    """Exception raised when I{virsh} command fail due to bad command or options."""
    pass


class KVM(Host):
    """Class used for managing KVM physical host."""
    def __init__(self, host, confs_path, disks_path):
        """Herit current object from B{Host} and check it is a KVM host (ie:
        module I{kvm} is loaded.

        @type host: Host
        @param host: Host object of the KVM host.
        @type confs_path: str
        @param confs_path: Directory where configurations are stored.
        @type disks_path: str
        @param disks_path: Directory where disks images are stored.
        """
        Host.__init__(self, host)
#        self.__dict__.update(host.__dict__)
        if not self.loaded('kvm'):
            raise KVMError('not a KVM host')
        self.conf = confs_path
        self.disks = disks_path


    def virsh(self, command, params=[], options=[]):
        """Execute I{virsh} command and check stderr for knowing if command failed
        of if an invalid commad/options are passed.

        command: C{virsh I{command} I{params} I{options}}

        @type command: str
        @param command: Virsh command (start, shutdown, define, ...)
        @type params: list
        @param params: Virsh command parameters.
        @type options: list
        @param options: Virsh command options.

        @rtype: list
        @return: status, stdout, stderr
        """
        virsh_cmd = ' '.join((
            'virsh',
            command,
            ' '.join(params),
            ' '.join(options)
        ))
        status, stdout, stderr = self.execute(virsh_cmd)
        if not status \
        and (UNKNOWN_CMD_REGEXP.match(stderr) or BAD_OPTION_REGEXP.match(stderr)):
            raise VirshError(stderr)
        return (status, stdout, stderr)


    def list(self):
        """List VM defining in the host.

        command: C{virsh list --all}

        @rtype: list
        @return: List of the VMs.
        """
        vms = self.virsh('list', ('--all',))[1]
        return [vm.split()[1] for vm in vms.split('\n')[2:-2]]


    def exist(self, vm):
        """Check if given VM name exist.

        @type vm: str
        @param vm: Name of the VM to check.

        @rtype: boolean
        @return: I{True} if VM exists, I{False} otherwise.
        """
        if vm not in self.list():
            return False
        return True



class VMError(Exception):
    """Base exception for VM error."""
    pass

class VMNotExist(VMError):
    """Exception raised if a VM not exists."""
    pass

class ConfigError(VMError):
    """Exception raised if there are errors in configuration."""
    pass


class VM(Host):
    """Class for managing KVM virtual machines."""
    RUNNING = 'running'
    IDLE = 'idle'
    PAUSED = 'paused'
    SHUTDOWN = 'shutdown'
    SHUTOFF = 'shut off'
    CRASHED = 'crashed'
    DYING = 'dying'

    def __init__(self, name, parent, disk='', host=None):
        """Initialize VM.

        @type name: str
        @param name: Name of the VM.
        @type parent: KVM
        @param parent: KVM object of the parent.
        @type host: Host
        @param host: Host
        """
        Host.__init__(self)
        if host:
            self.__dict__.update(host.__dict__)
        self.name = name
        self.parent = parent
        if not parent.ssh:
            raise NotConnected, "no connection on KVM host"
        self.conf_file = os.path.join(self.parent.conf, '%s.xml' % self.name)
        self.cores = 2
        self.memory = 1
        default_disk = os.path.join(self.parent.disks, '%s.qcow2' % self.name)
        if disk:
            default_disk = disk
        self.disks = [default_disk,]
        self.interfaces = []
        self.mounted_lvs = []


    def _exist(self):
        """Raise an  exception if VM not exists on parent."""
        if not self.parent.exist(self.name):
            raise VMNotExist


    def state(self):
        """Return the state of the VM.

        command: C{virsh domstate I{vm}}

        @rtype: str
        @return: State of the VM.
        """
        self._exist()
        return self.parent.virsh('domstate', (self.name,))[1].split('\n')[0]


    def started(self):
        """Check if VM is started.

        @rtype: boolean
        @return: I{True} if VM is started, I{False} otherwise.
        """
        return True if self.state() == self.RUNNING else False


    def start(self):
        """Start the VM.

        command: C{virsh start I{vm}}

        @rtype: list
        @return: status, stdout, stderr
        """
        self._exist()
        return self.parent.virsh('start', (self.name,))


    def stop(self, timeout=20, force=False):
        """Stop the VM. If VM not stopped after I{timeout} and I{force} set to
        I{True}, the VM is destroyed.

        command: C{virsh shutdown I{vm}}

        @type timeout: int
        @param timeout: Timeout before considering shutdow failed.
        @type force: boolean
        @param force: Destroy the VM if stop fail.

        @rtype: list
        @return: status, stdout, stderr
        """
        self._exist()
        if not self.started():
            return (True, '', 'VM was already stopped')

        output = self.parent.virsh('shutdown', (self.name,))
        if not output[0]:
            return output

        def timeout_handler(signum, frame):
            raise TimeoutException()
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            while self.state() != self.SHUTOFF:
                pass
        except TimeoutException:
            if force:
                status, stdout, stderr = self.destroy()
                stderr = 'the vm has been destroyed after %ss' % timeout if status else stderr
                return (status, stdout, stderr)
            else:
                return (False, '', 'the vm does not stop after %ss' % timeout)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)

        return (True, 'vm stopped', '')


    def destroy(self):
        """Destroy the VM.

        command:  C{virsh destroy I{vm}}

        @rtype: list
        @return: status, stdout, stderr
        """
        return self.parent.virsh('destroy', (self.name,))


    def define(self):
        """Define a VM.

        command: C{virsh define I{vm}.xml}

        @rtype: list
        @return: status, stdout, stderr
        """
        return self.parent.virsh('define', (self.conf_file,))


    def undefine(self):
        """Undefine a VM.

        command: C{virsh undefine I{vm}}

        @rtype: list
        @return: status, stdout, stderr
        """
        return self.parent.virsh('undefine', (self.name,))


    def mount(self, dest='/tmp', vggroup='sys', lvroot='root'):
        """Mount the disk image of a VM.

        This method execute sequentialy:
            - C{qemy-nbd -c /dev/nbd1 I{vm_disk}} for charging disk image
            - C{vgchange -ay I{vggroup}} for activating volume group
            - C{lvdisplay I{vggroup}} for retrieving logical volumes
            - C{mount /dev/I{vgroot}/I{lvroot} I{dest}} for mounting root filesystem
            - for each logical volumes I{lv} except swap:
                - C{mount /dev/I{vggroup}/I{lv} I{dest}/I{lv}} for mounting filesystem

        It added to the object the attribut I{mounted_lvs} that is a list containing
        all mountpoints and which the first element is mountpoint of the root filesystem.

        @type dest: str
        @param dest: Directory on which mount image.
        @type vggroup: str
        @param vggroup: LVM volume group
        @type lvroot: str
        @param lvroot: LVM logical volume for root filesystem.

        @rtype: list
        @return: status, stdout, stderr
        """
        # Read qcow2 image
        status, stdout, stderr = self.parent.execute('qemu-nbd -c /dev/nbd1 %s' % self.disks[0])
        if not status:
            return (
                False,
                '',
                "'qemu-nbd -c' command failed with error:\n'%s'" % stderr.strip()
            )
        time.sleep(2)

        # Activate LVM volume groups.
        status, stdout, stderr = self.parent.execute('vgchange -ay %s' % vggroup)
        if not status:
            return(
                False,
                '',
                "unable to activate new LVM volume group:\n'%s'" % stderr.strip()
            )

        # Get LVM logical volume.
        status, stdout, stderr = self.parent.execute('lvdisplay %s' % vggroup)
        if not status:
            return(
                False,
                '',
                "unable to get LVM logical volume for volume group '%s':\n%s" % (
                    vggroup,
                    stderr.strip()
                )
            )
        lines = stdout.split('\n')
        lvs = [
            line.split()[2].split('/')[3] for line in lines if line.find('LV Name') != -1
        ]
        try:
            lvs.remove(lvroot)
            lvs.remove('swap')
        except ValueError:
            pass

        # Mount logical volumes.
        lvroot_mountpoint = os.path.join(dest, self.name)
        self.parent.mkdir(lvroot_mountpoint)
        lvroot_path = os.path.join('/dev', vggroup, lvroot)
        status, stdout, stderr = self.parent.execute('mount %s %s' % (
            lvroot_path,
            lvroot_mountpoint)
        )
        if not status:
            return (
                False,
                '',
                "unable to mount root logical volume '%s' in '%s':\n%s" %(
                    lvroot_path,
                    lvroot_mountpoint,
                    stderr.strip()
                )
            )
        self.mounted_lvs.append(lvroot_mountpoint)

        mount_errors = []
        for lv_name in lvs:
            lv_path = os.path.join('/dev', vggroup, lv_name)
            lv_mountpoint = os.path.join(lvroot_mountpoint, lv_name)
            self.parent.mkdir(lv_mountpoint)
            status, stdout, stderr = self.parent.execute('mount %s %s' % (lv_path, lv_mountpoint))
            if not status:
                mount_errors.append("unable to mount logical volume '%s' in '%s':\n%s" % (
                    lv_path,
                    lv_mountpoint,
                    stderr.strip()
                ))
                continue
            self.mounted_lvs.append(lv_mountpoint)

        stderr = ''
        if mount_errors:
            stderr = '\n'.join([error for error in mount_errors])

        return (True, 'logical volumes find: %s' % ', '.join(lvs), stderr)


    def umount(self, vggroup='sys'):
        # Umount mounting volumes.
        reverse_lvs = list(self.mounted_lvs)
        reverse_lvs.reverse()
        if self.mounted_lvs:
            for lv_mountpoint in reverse_lvs:
                self.parent.execute('umount %s' % lv_mountpoint)
                self.mounted_lvs.remove(lv_mountpoint)
        del(reverse_lvs)

        # If remaining mount points, deactivation of LVM logical volumes will failed.
        if self.mounted_lvs:
            return (False, '', 'remaining mountpoints: %s' % ', '.join(self.mounted_lvs))

        status, stdout, stderr = self.parent.execute('vgchange -an %s' % vggroup)
        if not status:
            return (False, '', 'unable to disable logical volumes')

        status, stdout, stderr = self.parent.execute('qemu-nbd -d /dev/nbd1')
        if not status:
            return (False, '', "'qemu-ndb -d' command failed with error:\n'%s'" % stderr.strip())

        return (True, '', '')


    def get_conf(self):
        self._exist()

        dom = parseString(self.parent.read(self.conf_file))
        name = dom.getElementsByTagName('name')[0].childNodes[0].data
        uuid = dom.getElementsByTagName('uuid')[0].childNodes[0].data
        memory = dom.getElementsByTagName('memory')[0].childNodes[0].data
        cpu = dom.getElementsByTagName('vcpu')[0].childNodes[0].data

        disks = []
        disks_nodes = dom.getElementsByTagName('disk')
        for disk_node in disks_nodes:
            disk_type = disk_node.getAttribute('device')
            if disk_type != 'disk':
                continue
            disks.append(disk_node.getElementsByTagName('source')[0].getAttribute('file'))

        return {
            'name': name,
            'uuid': uuid,
            'memory': memory,
            'cpu': cpu,
            'disks': disks
        }

    def gen_uuid(self):
        return '-'.join((
            ''.join([random.choice(CHOICES) for i in xrange(0, 8)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 4)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 12)]),
        ))


    def gen_mac(self):
        return ':'.join((
            '54', '52', '00',
            ''.join([random.choice(CHOICES) for i in xrange(0, 2)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 2)]),
            ''.join([random.choice(CHOICES) for i in xrange(0, 2)])
        ))


    def node(self, name, attrs={}, text='', childs=[]):
        node = self.xml.createElement(name)
        for attr_name, attr_value in attrs.iteritems():
            node.setAttribute(attr_name, attr_value)
        if text:
            node.appendChild(self.xml.createTextNode(text))
        if childs:
            for child_node in childs:
                node.appendChild(child_node)
        return node


    def get_interfaces_config(self):
        if not self.interfaces:
            raise ConfigError("no network interfaces defined")

        interface_nodes = []
        for interface in self.interfaces:
            vlan = interface['vlan']
            interface_nodes.append(self.node('interface', {'type': 'bridge'}, childs=(
                self.node('mac', {'address': self.gen_mac()}),
                self.node('source', {'bridge': 'br%s' % vlan}),
                self.node('model', {'type': 'virtio'}),
                self.node('address', {
                    'type': 'pci',
                    'domain': '0x0000',
                    'bus': '0x00',
                    'slot': '0x03',
                    'function': '0x0'
                })
            )))
        return interface_nodes


    def get_devices_config(self):
        devices_nodes = [
            self.node('emulator', text='/usr/bin/kvm'),
            self.node('disk', {'type': 'file', 'device': 'disk'}, childs=(
                   self.node('driver', {'name': 'qemu', 'type': 'qcow2'}),
                   self.node('source', {'file': self.disks[0]}),
                   self.node('target', {'dev': 'vda', 'bus': 'virtio'})
            ))
        ]
        devices_nodes.extend(self.get_interfaces_config())
        devices_nodes.extend((
            self.node('serial', {'type': 'pty'}, childs=(
                self.node('target', {'port': '0'}),
            )),
            self.node('console', {'type': 'pty'}, childs=(
                self.node('target', {'port': '0'}),
            )),
            self.node('input', {'type': 'mouse', 'bus': 'ps2'}),
            self.node('graphics', {
                'type': 'vnc',
                'port': '-1',
                'autoport': 'yes',
                'keymap': 'fr'}
            ),
            self.node('sound', {'model': 'es1370'}),
            self.node('video', childs=(
                self.node('model', {'type': 'cirrus', 'vram': '9216', 'heads': '1'}),
            )
        )))
        return devices_nodes


    def gen_conf(self, path=''):
        # Hack for not printing xml version
        Document.writexml = writexml_document

        # Hack for XML output: text node on one line
        Element.writexml = writexml_element

        self.xml = Document()
        memory_value = str(int(float(self.memory) * 1024 * 1024))

        config = self.node('domain', {'type': 'kvm'}, childs=(
            self.node('name', text=self.name),
            self.node('uuid', text=self.gen_uuid()),
            self.node('memory', text=memory_value),
            self.node('currentMemory', text=memory_value),
            self.node('vcpu', text=str(self.cores)),
            self.node('os', childs=(
                self.node('type', {
                    'arch': 'x86_64',
                    'machine': 'pc-0.11'
                }, 'hvm'),
                self.node('boot', {'dev': 'hd'})
            )),
            self.node('features', childs=(
                self.node('acpi'),
                self.node('apic'),
                self.node('pae')
            )),
            self.node('clock', {'offset': 'utc'}),
            self.node('on_poweroff', text='destroy'),
            self.node('on_reboot', text='restart'),
            self.node('on_crash', text='restart'),
            self.node('devices', childs=self.get_devices_config())
        ))

        filepath = path if path else self.conf_file
        return self.parent.write(
            filepath,
            '\n'.join(config.toprettyxml(indent='  ').split('\n')[1:])
        )


    def set_hosts_file(self):
        return self.parent.write(
            os.path.join(self.mounted_lvs[0], 'etc', 'hosts'),
            '\n'.join((
                '127.0.0.1       localhost',
                '%s       %s.u-strasbg.fr     %s' % (
                    self.interfaces[0]['ip'],
                    self.name,
                    self.name
                ),
                '',
                '# The following lines are desirable for IPv6 capable hosts',
                '::1     localhost ip6-localhost ip6-loopback',
                'fe00::0 ip6-localnet',
                'ff00::0 ip6-mcastprefix',
                'ff02::1 ip6-allnodes',
                'ff02::2 ip6-allrouters'
            ))
        )


    def set_password(self, username, password):
        return self.parent.set_password(
            username,
            password,
            os.path.join(self.mounted_lvs[0], 'etc', 'shadow')
        )



class UbuntuVM(VM):
    def __init__(self, name, parent, host=None):
        VM.__init__(self, name, parent, host)


    def set_hostname(self):
        return self.parent.write(
            os.path.join(self.mounted_lvs[0], 'etc', 'hostname'),
            self.name
        )


    def set_network(self):
        network_conf = '\n'.join((
            'auto lo',
            'iface lo inet loopback',
            '\n'
        ))

        counter = 0
        for interface in self.interfaces:
            interface_name = 'eth%s' % counter

            try:
                ip = interface['ip']
                netmask = interface['netmask']
            except KeyError:
                raise ConfigError('bad interface configuration')
            gateway = interface['gateway'] if 'gateway' in interface else ''

            interface_conf = [
                'auto %s' % interface_name,
                'iface %s inet static' % interface_name,
                '    address %s' % ip,
                '    netmask %s' % netmask,
                '\n',
            ]
            if gateway:
                interface_conf.insert(-2, '    gateway %s' % gateway)
            network_conf += '\n'.join(interface_conf)
            counter += 1

        root = self.mounted_lvs[0]
        output = self.parent.write(
            os.path.join(root, 'etc', 'network', 'interfaces'),
            network_conf
        )
        if not output[0]:
            return output

        try:
            self.parent.rm(os.path.join(
                root,
                'etc',
                'udev',
                'rules.d',
                '70-persistent-net.rules'
            ))
            return (True, '', '')
        except OSError, os_err:
            return (False, '', os_err)


    def set_mail_conf(self):
        pass


class RedhatVM(VM):
    def __init__(self, name, parent, host=None):
        VM.__init__(self, name, parent, host)


    def set_hostname(self):
        return self.parent.write(
            os.path.join(self.mounted_lvs[0], 'etc', 'sysconfig', 'network'),
            "\n".join((
                'NETWORKING=yes',
                'NETWORKING_IPV6=no',
                'HOSTNAME=%s' % self.name
            ))
        )


    def set_network(self):
        root = self.mounted_lvs[0]
        network_root = os.path.join(root, 'etc', 'sysconfig', 'network-scripts')
        self.parent.rm(os.path.join(network_root, 'ifcfg-ext'))
        counter = 0
        for interface in self.interfaces:
            if len(interface) == 3:
                ip, netmask = interface[:2]
                gateway = ''
            elif len(interface) == 4:
                ip, netmask, gateway = interface[:3]
            else:
                raise ConfigError('bad interface configuration')

            interface_conf = [
                'DEVICE=eth%s' % counter,
                'BOOTPROTO=none',
                'ONBOOT=yes',
                'NETMASK=%s' % netmask,
                'IPADDR=%s' % ip,
                'TYPE=Ethernet',
                'USERCTL=no',
                'IPV6INIT=no',
                'PEERDNS=yes',
            ]
            if gateway:
                interface_conf.insert(5, 'GATEWAY=%s' % gateway)

            output = self.parent.write(
                os.path.join(network_root, 'ifcfg-eth%s' % counter),
                "\n".join(interface_conf)
            )
            counter += 1
            if not output[0]:
                return output
        return (True, '', '')


    def set_mail_conf(self):
        return (True, '', '')
