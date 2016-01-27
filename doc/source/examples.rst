********
Examples
********

.. code::

    >>> import unix, kvm
    >>> host = unix.Remote()
    >>> host.connect('remote_host')
    >>> host = kvm.Hypervisor(host)

This is for testing purpose. In general, it is probably better to use
the ``unix.connect`` context manager (which close the connection at when
quitting):

.. code::

    with unix.connect('remote_host') as host:
        host = kvm.Hypervisor(host)

Managing the hypervisor
=======================
Virsh version
~~~~~~~~~~~~~
.. code::

    >>> host.hypervisor.version()
    {'compiled_against_library': 'libvirt 1.2.2',
     'running_hypervisor': 'QEMU 2.0.0',
     'using_api': 'QEMU 1.2.2',
     'using_library': 'libvirt 1.2.2'}

URI
~~~
.. code::

    >>> host.hypervisor.uri()
    'qemu:///system'

System information
~~~~~~~~~~~~~~~~~~
.. code::

    >>> host.hypervisor.sysinfo()
    {'bios': {'date': '02/06/2014', 'vendor': 'HP', 'version': 'A28'},
     'memory_device': [{'bank_locator': 'Not Specified',
       'form_factor': 'DIMM',
       'locator': 'Proc 1 DIMM 1A',
       'manufacturer': 'HP',
       'part_number': '647650-171',
       'serial_number': 'Not Specified',
       'size': '8192 MB',
       'speed': '1333 MHz',
       'type': 'DDR3',
       'type_detail': 'Synchronous Registered (Buffered)'},
      {'bank_locator': 'Not Specified',
       'form_factor': 'DIMM',
       'locator': 'Proc 1 DIMM 3E',
       'manufacturer': 'HP',
       'part_number': '647650-171',
       'serial_number': 'Not Specified',
       'size': '8192 MB',
       'speed': '1333 MHz',
       'type': 'DDR3',
       'type_detail': 'Synchronous Registered (Buffered)'},
      ...
      {'bank_locator': 'Not Specified',
       'form_factor': 'DIMM',
       'locator': 'Proc 2 DIMM 12H',
       'manufacturer': 'HP',
       'part_number': '647650-171',
       'serial_number': 'Not Specified',
       'size': '8192 MB',
       'speed': '1333 MHz',
       'type': 'DDR3',
       'type_detail': 'Synchronous Registered (Buffered)'}],
     'processor': [{'external_clock': '200 MHz',
       'family': 'Opteron',
       'manufacturer': 'AMD',
       'max_speed': '3500 MHz',
       'part_number': 'Not Specified',
       'serial_number': 'Not Specified',
       'signature': 'Family 21, Model 2, Stepping 0',
       'socket_destination': 'Proc 1',
       'status': 'Populated, Enabled',
       'type': 'Central Processor',
       'version': 'AMD Opteron(tm) Processor 6376'},
      {'external_clock': '200 MHz',
       'family': 'Opteron',
       'manufacturer': 'AMD',
       'max_speed': '3500 MHz',
       'part_number': 'Not Specified',
       'serial_number': 'Not Specified',
       'signature': 'Family 21, Model 2, Stepping 0',
       'socket_destination': 'Proc 2',
       'status': 'Populated, Idle',
       'type': 'Central Processor',
       'version': 'AMD Opteron(tm) Processor 6376'}],
     'system': {'family': 'ProLiant',
      'manufacturer': 'HP',
      'product': 'ProLiant DL385p Gen8',
      'serial': 'CZJ4020390',
      'sku': '703932-421',
      'uuid': '39333037-3233-5A43-4A34-303230333930',
      'version': 'Not Specified'},
     'type': 'smbios'}

Basic information about the node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

    >>> host.hypervisor.nodeinfo()
    {'cores_per_socket': 32,
     'cpu_frequency': '1400 MHz',
     'cpu_model': 'x86_64',
     'cpu_sockets': 1,
     'cpus': 32,
     'memory_size': '131919564 KiB',
     'numa_cells': 1,
     'threads_per_core': 1}

CPU map
~~~~~~~
.. code::

    >>> host.hypervisor.nodecpumap()
    {'cpu_map': 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy',
     'cpus_online': 32,
     'cpus_present': 32}

CPU stats
~~~~~~~~~
.. code::

    >>> host.hypervisor.nodecpustats()
    {'idle': 67050204750000000,
     'iowait': 47793370000000,
     'system': 1004314090000000,
     'user': 2927654340000000}

    >>> host.hypervisor.nodecpustats(percent=True)
    {'idle': '90.3%',
     'iowait': '0.1%',
     'system': '1.8%',
     'usage': '9.6%',
     'user': '7.8%'}

    >>> host.hypervisor.nodecpustats(31, percent=True)
    {'idle': '97.0%',
     'iowait': '0.0%',
     'system': '1.0%',
     'usage': '3.0%',
     'user': '2.0%'}

Memory stats
~~~~~~~~~~~~
.. code::

    >>> host.hypervisor.nodememstats()
    {'buffers': '246688 KiB',
     'cached': '97146740 KiB',
     'free': '2155148 KiB',
     'total': '131919564 KiB'}

    >>> host.hypervisor.nodememstats(0)
    {'free': '1138132 KiB', 'total': '32848952 KiB'}

Tune memory parameters
~~~~~~~~~~~~~~~~~~~~~~
.. code::

    >>> host.hypervisor.node_memory_tune()
    {'shm_full_scans': 138,
     'shm_merge_across_nodes': 1,
     'shm_pages_shared': 424645,
     'shm_pages_sharing': 3721845,
     'shm_pages_to_scan': 100,
     'shm_pages_unshared': 3907333,
     'shm_pages_volatile': 2108845,
     'shm_sleep_millisecs': 200}

    >>> host.hypervisor.node_memory_tune(shm_pages_to_scan=150, shm_sleep_millisecs=100)
    (True, '', '')

    >>> host.hypervisor.node_memory_tune()
    {'shm_full_scans': 138,
     'shm_merge_across_nodes': 1,
     'shm_pages_shared': 424622,
     'shm_pages_sharing': 3721888,
     'shm_pages_to_scan': 150,
     'shm_pages_unshared': 3910168,
     'shm_pages_volatile': 2105990,
     'shm_sleep_millisecs': 100}

Suspend host
~~~~~~~~~~~~
.. code::

    >>> host.hypervisor.nodesuspend('mem', 60)
    (True, '', '')

Capabilities
~~~~~~~~~~~~
.. code::

    >>> kvm.pprint(host.hypervisor.capabilities())
    {'guest': [{'arch': {'@name': 'i686',
        'domain': [{'@type': 'qemu'},
         {'@type': 'kvm',
          'emulator': '/usr/bin/kvm-spice',
          'machine': [{'#text': 'pc',
            '@canonical': 'pc-i440fx-trusty',
            '@maxCpus': '255'},
           {'#text': 'pc-1.3', '@maxCpus': '255'},
           ...
           {'#text': 'pc-0.13', '@maxCpus': '255'}]}],
        'emulator': '/usr/bin/qemu-system-i386',
        'machine': [{'#text': 'pc',
          '@canonical': 'pc-i440fx-trusty',
          '@maxCpus': '255'},
         {'#text': 'pc-0.12', '@maxCpus': '255'},
         ...
         {'#text': 'pc-0.13', '@maxCpus': '255'}],
        'wordsize': '32'},
       'features': {'acpi': {'@default': 'on', '@toggle': 'yes'},
        'apic': {'@default': 'on', '@toggle': 'no'},
        'cpuselection': True,
        'deviceboot': True,
        'nonpae': True,
        'pae': True},
       'os_type': 'hvm'},
      {'arch': {'@name': 'x86_64',
        'domain': [{'@type': 'qemu'},
         {'@type': 'kvm',
          'emulator': '/usr/bin/kvm-spice',
          'machine': [{'#text': 'pc',
            '@canonical': 'pc-i440fx-trusty',
            '@maxCpus': '255'},
           {'#text': 'pc-1.3', '@maxCpus': '255'},
           ...
           {'#text': 'pc-0.13', '@maxCpus': '255'}]}],
        'emulator': '/usr/bin/qemu-system-x86_64',
        'machine': [{'#text': 'pc',
          '@canonical': 'pc-i440fx-trusty',
          '@maxCpus': '255'},
         {'#text': 'pc-1.3', '@maxCpus': '255'},
         ...
         {'#text': 'pc-0.13', '@maxCpus': '255'}],
        'wordsize': '64'},
       'features': {'acpi': {'@default': 'on', '@toggle': 'yes'},
        'apic': {'@default': 'on', '@toggle': 'no'},
        'cpuselection': True,
        'deviceboot': True},
       'os_type': 'hvm'}],
     'host': {'cpu': {'arch': 'x86_64',
       'feature': [{'@name': 'bmi1'},
        {'@name': 'perfctr_nb'},
        {'@name': 'perfctr_core'},
        {'@name': 'topoext'},
        {'@name': 'nodeid_msr'},
        {'@name': 'tce'},
        {'@name': 'lwp'},
        {'@name': 'wdt'},
        {'@name': 'skinit'},
        {'@name': 'ibs'},
        {'@name': 'osvw'},
        {'@name': 'cr8legacy'},
        {'@name': 'extapic'},
        {'@name': 'cmp_legacy'},
        {'@name': 'fxsr_opt'},
        {'@name': 'mmxext'},
        {'@name': 'osxsave'},
        {'@name': 'monitor'},
        {'@name': 'ht'},
        {'@name': 'vme'}],
       'model': 'Opteron_G5',
       'topology': {'@cores': '32', '@sockets': '1', '@threads': '1'},
       'vendor': 'AMD'},
      'migration_features': {'live': True,
       'uri_transports': {'uri_transport': 'tcp'}},
      'power_management': {'suspend_disk': True, 'suspend_hybrid': True},
      'secmodel': [{'doi': '0', 'model': 'apparmor'},
       {'baselabel': [{'#text': '+110:+117', '@type': 'kvm'},
         {'#text': '+110:+117', '@type': 'qemu'}],
        'doi': '0',
        'model': 'dac'}],
      'topology': {'cells': {'@num': '4',
        'cell': [{'@id': '0',
          'cpus': {'@num': '8',
           'cpu': [{'@core_id': '0',
             '@id': '0',
             '@siblings': '0,2',
             '@socket_id': '0'},
            {'@core_id': '1', '@id': '2', '@siblings': '0,2', '@socket_id': '0'},
            {'@core_id': '2', '@id': '4', '@siblings': '4,6', '@socket_id': '0'},
            {'@core_id': '3', '@id': '6', '@siblings': '4,6', '@socket_id': '0'},
            {'@core_id': '4', '@id': '8', '@siblings': '8,10', '@socket_id': '0'},
            {'@core_id': '5', '@id': '10', '@siblings': '8,10', '@socket_id': '0'},
            {'@core_id': '6',
             '@id': '12',
             '@siblings': '12,14',
             '@socket_id': '0'},
            {'@core_id': '7',
             '@id': '14',
             '@siblings': '12,14',
             '@socket_id': '0'}]},
          'memory': {'#text': '32848952', '@unit': 'KiB'}},
         {'@id': '1',
          'cpus': {'@num': '8',
           'cpu': [{'@core_id': '0',
             '@id': '16',
             '@siblings': '16,18',
             '@socket_id': '0'},
            ....
            {'@core_id': '7',
             '@id': '30',
             '@siblings': '28,30',
             '@socket_id': '0'}]},
          'memory': {'#text': '33029144', '@unit': 'KiB'}},
         {'@id': '2',
          'cpus': {'@num': '8',
           'cpu': [{'@core_id': '0',
             '@id': '1',
             '@siblings': '1,3',
             '@socket_id': '1'},
            ...
            {'@core_id': '7',
             '@id': '15',
             '@siblings': '13,15',
             '@socket_id': '1'}]},
          'memory': {'#text': '33029148', '@unit': 'KiB'}},
         {'@id': '3',
          'cpus': {'@num': '8',
           'cpu': [{'@core_id': '0',
             '@id': '17',
             '@siblings': '17,19',
             '@socket_id': '1'},
            ...
            {'@core_id': '7',
             '@id': '31',
             '@siblings': '29,31',
             '@socket_id': '1'}]},
          'memory': {'#text': '33012320', '@unit': 'KiB'}}]}},
      'uuid': '39333037-3233-5a43-4a34-303230333930'}}

.. note:: By default the method that parse XML files return an **OrderedDict** for keeping order. ``kvm.pprint()`` function allow to pretty print **OrderedDict** dicts.

Freecell
~~~~~~~~
.. code::

    >>> host.hypervisor.freecell(all=True)
    {'0': '1034804 KiB',
     '1': '501332 KiB',
     '2': '268616 KiB',
     '3': '322696 KiB',
     'total': '2127448 KiB'}

    >>> host.hypervisor.freecell(cellno=0)
    {'0': '1020744 KiB'}

Managing interfaces
===================
List
~~~~
.. code::

    >>> host.list_interfaces()
    {'br0': {'mac': '64:70:02:00:6a:95', 'state': 'active'},
     'lo': {'mac': '00:00:00:00:00:00', 'state': 'active'}}

Conf
~~~~
.. code::

    >>> kvm.pprint(host.iface.conf('br0'))
    {'@name': 'br0',
     '@type': 'bridge',
     'bridge': {'interface': {'@name': 'enp3s5',
       '@type': 'ethernet',
       'link': {'@speed': '1000', '@state': 'up'},
       'mac': {'@address': '64:70:02:00:6a:95'}}},
     'protocol': [{'@family': 'ipv4',
       'ip': {'@address': '192.168.0.10', '@prefix': '24'}},
      {'@family': 'ipv6',
       'ip': {'@address': 'fe80::6670:2ff:fe00:6a95', '@prefix': '64'}}]}

Managing networks
=================
List
~~~~
.. code::

    >>> host.list_networks(all=True)
    {'default': {'autostart': True, 'persistent': True, 'state': 'active'}}

Conf
~~~~
.. code::

    >>> kvm.pprint(host.net.conf('default'))
    {'bridge': {'@delay': '0', '@name': 'virbr0', '@stp': 'on'},
     'forward': {'@mode': 'nat',
      'nat': {'port': {'@end': '65535', '@start': '1024'}}},
     'ip': {'@address': '192.168.122.1',
      '@netmask': '255.255.255.0',
      'dhcp': {'range': {'@end': '192.168.122.254', '@start': '192.168.122.2'}}},
     'mac': {'@address': '52:54:00:d1:7f:f7'},
     'name': 'default',
     'uuid': '403015c8-8339-4a66-bc37-ec794bc39e9d'}

Destroy (stop)
~~~~~~~~~~~~~~
.. code::

    >>> host.net.destroy('default')
    (True, 'Network default destroyed', '')

    >>> host.list_networks(all=True)
    {'default': {'autostart': True, 'persistent': True, 'state': 'inactive'}}

Undefine
~~~~~~~~
.. code::

    >>> host.net.undefine('default')
    (True, 'Network default has been undefined', '')

    >>> host.list_networks(all=True)
    {}

Create
~~~~~~
.. code::

    >>> net = {'name': 'br0', 'forward': {'@mode': 'bridge'}, 'bridge': {'@name': 'br0'}}
    >>> with host.open('/vm/conf/networks/br0.xml', 'w') as fhandler:
    ...    fhandler.write(kvm.to_xml('network', net))

    >>> host.network.define('/vm/conf/networks/br0.xml')
    (True, 'Network br0 defined from /vm/conf/networks/br0.xml', '')

    >>> host.network.autostart('br0')
    (True, 'Network br0 marked as autostarted', '')

    >>> host.network.start('br0')
    (True, 'Network br0 started', '')

    >>> host.list_networks()
    {'br0': {'autostart': True, 'persistent': True, 'state': 'active'}}

Managing storage pools
======================
List
~~~~
.. code::

    >>> host.list_pools(all=True)
    {}

Define
~~~~~~
.. code::

    >>> pool = {'@type': 'dir',
                'name': 'default',
                'source': True,
                 'target': {'path': '/vm/disk',
                             'permissions': {'group': '-1',
                                           'mode': '0711',
                                           'owner': '-1'}}}
    >>> with host.open('/tmp/pool.xml', 'w') as fhandler:
    ...     fhandler.write(kvm.to_xml('pool', pool))
    >>> host.pool.define('/tmp/pool.xml')
    (True, 'Pool default defined from /tmp/pool.xml', '')

    >>> host.list_pools(all=True, details=True)
    {'default': {'allocation': '-',
      'autostart': False,
      'available': '',
      'capacity': '- -',
      'persistent': True,
      'state': 'inactive'}}

Build
~~~~~
.. code::

    >>> host.listdir('/vm')
    []

    >>> host.pool.build('default')
    (True, 'Pool default built', '')

    >>> host.listdir('/vm')
    ['disk']

Start
~~~~~
.. code::

    >>> host.pool.start('default')
    (True, 'Pool default started', '')

    >>> host.list_pools(all=True, details=True)
    {'default': {'allocation': '2.48 GiB',
      'autostart': False,
      'available': '11.14 GiB',
      'capacity': '13.62 GiB',
      'persistent': True,
      'state': 'running'}}

Autostart
~~~~~~~~~
.. code::

    >>> host.pool.autostart('default')
    (True, 'Pool default marked as autostarted', '')

    >>> host.list_pools(all=True)
    {'default': {'autostart': True, 'state': 'active'}}

    >>> host.pool.autostart('default', disable=True)
    (True, 'Pool default unmarked as autostarted', '')

    >>> host.list_pools(all=True)
    {'default': {'autostart': False, 'state': 'active'}}

Info
~~~~
.. code::

    >>> host.pool.info('default')
    {'allocation': '2.48 GiB',
     'autostart': False,
     'available': '11.14 GiB',
     'capacity': '13.62 GiB',
     'name': 'default',
     'persistent': True,
     'state': 'running',
     'uuid': '28d614d5-7e17-40fc-b866-cc4bd26eab47'}

Conf
~~~~
.. code::

    >>> kvm.pprint(host.pool.conf('default'))
    {'@type': 'dir',
     'allocation': {'#text': '2663366656', '@unit': 'bytes'},
     'available': {'#text': '11965825024', '@unit': 'bytes'},
     'capacity': {'#text': '14629191680', '@unit': 'bytes'},
     'name': 'default',
     'source': True,
     'target': {'path': '/vm/disk',
      'permissions': {'group': '0', 'mode': '0711', 'owner': '0'}},
     'uuid': '28d614d5-7e17-40fc-b866-cc4bd26eab47'}

Uuid
~~~~
.. code::

    >>> host.pool.uuid('default')
    '28d614d5-7e17-40fc-b866-cc4bd26eab47'

Name
~~~~
.. code::

    >>> host.pool.name('28d614d5-7e17-40fc-b866-cc4bd26eab47')
    'default'

Destroy
~~~~~~~
.. code::

    >>> host.pool.destroy('default')
    (True, 'Pool default destroyed', '')

    >>> host.list_pools(all=True)
    {'default': {'autostart': False, 'state': 'inactive'}}

Undefine
~~~~~~~~
.. code::

    >>> host.pool.undefine('default')
    (True, 'Pool default has been undefined', '')

    >>> host.list_pools(all=True)
    {}

Create
~~~~~~
.. code::

    >>> host.pool.create('/tmp/pool.xml')
    (True, 'Pool default created from /tmp/pool.xml', '')

    >>> host.list_pools(all=True, details=True)
    {'default': {'allocation': '2.48 GiB',
      'autostart': False,
      'available': '11.14 GiB',
      'capacity': '13.62 GiB',
      'persistent': False,
      'state': 'running'}}

Delete
~~~~~~


Managing volumes
================
Create
~~~~~~
.. code::

    >>> host.volume.create_as('default', 'disk.qcow2', '20G', format='qcow2')
    (True, 'Vol disk.qcow2 created', '')

    >>> host.list_volumes('default', details=True)
    {'disk.qcow2': {'allocation': '196.00 KiB',
     'capacity': '20.00 GiB',
     'path': '/vm/disk/disk.qcow2',
     'type': 'file'}}

.. code::

    >>> vol = {'@type': 'file',
               'capacity': {'#text': '5368709120', '@unit': 'bytes'},
               'key': '/vm/disk/disk3.qcow2',
               'name': 'disk3.qcow2',
               'source': True,
               'target': {'format': {'@type': 'qcow2'}, 'path': '/vm/disk/disk3.qcow2'}}

    >>> with host.open('/tmp/volume.xml', 'w') as fhandler:
        fhandler.write(kvm.to_xml('volume', vol))

    >>> host.volume.create('default', '/tmp/volume.xml')
    (True, 'Vol disk3.qcow2 created from /tmp/volume.xml', '')

Delete
~~~~~~
.. code::

    >>> host.volume.delete('disk.qcow2', pool='default')
    (True, 'Vol disk.qcow2 deleted', '')

Info
~~~~
.. code::

    >>> host.volume.info('disk.qcow2', pool='default')
    {'allocation': '3.32 MiB',
     'capacity': '20.00 GiB',
     'name': 'disk.qcow2',
     'type': 'file'}

Conf
~~~~
.. code::

    >>> kvm.pprint(host.volume.conf('disk.qcow2', pool='default'))
    {'@type': 'file',
     'allocation': {'#text': '3485696', '@unit': 'bytes'},
     'capacity': {'#text': '21474836480', '@unit': 'bytes'},
     'key': '/vm/disk/disk.qcow2',
     'name': 'disk.qcow2',
     'source': True,
     'target': {'format': {'@type': 'qcow2'},
      'path': '/vm/disk/disk.qcow2',
      'permissions': {'group': '0', 'mode': '0600', 'owner': '0'},
      'timestamps': {'atime': '1453761773.202566393',
       'ctime': '1453761770.938733302',
       'mtime': '1453761770.918734776'}}}

Wipe
~~~~
.. code::

    >>> host.volume.wipe('disk.qcow2', pool='default', algorithm='dod')

.. note:: Other algorithms than *zero* need the ``scrub`` package to be installed.

Clone
~~~~~
.. code::

    >>> host.volume.clone('disk.qcow2', 'disk2.qcow2', pool='default', prealloc_metadata=True)
    (True, 'Vol disk2.qcow2 cloned from disk.qcow2', '')

    >>> host.list_volumes('default', details=True)
    {'disk.qcow2': {'allocation': '524.00 KiB',
      'capacity': '2.00 GiB',
      'path': '/vm/disk/disk.qcow2',
      'type': 'file'},
     'disk2.qcow2': {'allocation': '524.00 KiB',
      'capacity': '2.00 GiB',
      'path': '/vm/disk/disk2.qcow2',
      'type': 'file'}}

Resize
~~~~~~
.. code::

    >>> host.volume.resize('disk.qcow2', '5GiB', pool='default')
    (True, "Size of volume 'disk.qcow2' successfully changed to 5GiB", '')

    >>> host.list_volumes('default', details=True)
    {'disk.qcow2': {'allocation': '528.00 KiB',
      'capacity': '5.00 GiB',
      'path': '/vm/disk/disk.qcow2',
      'type': 'file'},
     'disk2.qcow2': {'allocation': '524.00 KiB',
      'capacity': '2.00 GiB',
      'path': '/vm/disk/disk2.qcow2',
      'type': 'file'}}

Upload/Download
~~~~~~~~~~~~~~~
.. code::

    >>> host.listdir('/vm')
    ['disk', 'modele-trusty.qcow2']

    >>> host.volume.create_as('default', 'trusty.qcow2', '1GiB')
    (True, 'Vol trusty.qcow2 created', '')

    >>> host.volume.upload(pool='default', file='/vm/modele-trusty.qcow2', vol='trusty.qcow2')
    (True, '', '')

    >>> host.list_volumes('default', details=True)
    {'trusty.qcow2': {'allocation': '1.83 GiB',
      'capacity': '30.00 GiB',
      'path': '/vm/disk/trusty.qcow2',
      'type': 'file'}}

    >>> host..volume.download(pool='default', file='/vm/new.qcow2', vol='trusty.qcow2')Out[205]: (True, '', '')

    >>> host.listdir('/vm')
    ['disk', 'modele-trusty.qcow2', 'new.qcow2']

Secrets
=======
Define
~~~~~~
.. code::

    >>> secret = {'@ephemeral': 'no',
    ...:          '@private': 'no',
    ...:          'uuid': kvm.gen
    ...:          'uuid': kvm.gen_uuid(),
    ...:          'usage': {'@type': 'volume',
    ...:                    'volume': '/vm/disk/encrypted.qcow2'}}

    >>> with host.open('/tmp/secret.xml', 'w') as fhandler:
    ...:     fhandler.write(kvm.to_xml('secret', secret))
    ...:

    >>> host.secret.define('/tmp/secret.xml')
    (True, 'Secret 6d14f73a-1087-7180-792d-8d80fc6b55ec created', '')

List
~~~~
.. code::

    >>> host.list_secrets()
    {'6d14f73a-1087-7180-792d-8d80fc6b55ec': 'volume /vm/disk/encrypted.qcow2'}

Conf
~~~~
.. code::

    >>> kvm.pprint(host.secret.conf('6d14f73a-1087-7180-792d-8d80fc6b55ec'))
    {'@ephemeral': 'no',
     '@private': 'no',
     'usage': {'@type': 'volume', 'volume': '/vm/disk/encrypted.qcow2'},
     'uuid': '6d14f73a-1087-7180-792d-8d80fc6b55ec'}

Set value
~~~~~~~~~
.. code::

    >>> import base64
    >>> passphrase = base64.b64encode(b'passphrase').decode()
    >>> host.secret.set_value('6d14f73a-1087-7180-792d-8d80fc6b55ec', passphrase)
    (True, 'Secret value set', '')

Get value
~~~~~~~~~
.. code::

    >>> base64.b64decode(host.secret.get_value('6d14f73a-1087-7180-792d-8d80fc6b55ec')).decode()
    'passphrase'

Undefine
~~~~~~~~~
.. code::

    >>> host.secret.undefine('6d14f73a-1087-7180-792d-8d80fc6b55ec')
    (True, 'Secret 6d14f73a-1087-7180-792d-8d80fc6b55ec deleted', '')

Managing domains
================
.. code::

    >>> domain = {'@type': 'kvm',
                  'name': 'trusty',
                  'uuid': kvm.gen_uuid(),
                  'title': 'Ubuntu 14.04',
                  'memory': {'@unit': 'GiB', '#text': 2},
                  'currentMemory': {'@unit': 'GiB', '#text': 2},
                  'vcpu': {'#text': 2},
                  'os': {'type': {'@arch': 'x86_64', '@machine': 'pc', '#text': 'hvm'},
                         'boot': {'@dev': 'hd'},
                         'bootmenu': {'@enable': 'no'}},
                  'features': {'acpi': None, 'apic': None, 'pae': None},
                  'clock': {'@offset': 'utc'},
                  'on_poweroff': {'#text': 'destroy'},
                  'on_reboot': {'#text': 'restart'},
                  'on_crash': {'#text': 'restart'},
                  'devices': {
                    'emulator': {'#text': '/usr/bin/kvm'},
                    'disk': [
                        {'@type': 'volume',
                         '@device': 'disk',
                         'driver': {'@name': 'qemu', '@type': 'qcow2'},
                         'source': {'@pool': 'default', '@volume': 'trusty.qcow2'},
                         'target': {'@dev': 'vda', '@bus': 'virtio'}}
                    ],
                    'interface': [
                        {'@type': 'network',
                         'mac': {'@address': kvm.gen_mac()},
                         'model': {'@type': 'virtio'},
                         'source': {'@network': 'br0'}}
                    ],
                    'serial': {'@type': 'pty', 'target': {'@port': 0}},
                    'console': {'@type': 'pty', 'target': {'@type': 'serial', '@port': 0}},
                    'input': [{'@type': 'mouse', '@bus': 'ps2'},
                              {'@type': 'keyboard', '@bus': 'ps2'}],
                    'graphics': {'@type': 'vnc',
                                 '@port': -1,
                                 '@autoport': 'yes',
                                 '@keymap': 'fr',
                                 'listen': {'@type': 'address', '@address': '127.0.0.1'}},
                    'video': {'model': {'@type': 'cirrus'}},
                    'memballon': {'@type': 'virtio'}
                  }
                  }

    >>> with host.open('/vm/conf/trusty.xml', 'w') as fhandler:
    ...     fhandler.write(kvm.to_xml('domain', domain))

    >>> host.domain.define('/vm/conf/trusty.xml')
    (True, 'Domain trusty defined from /vm/conf/trusty.xml', '')

    >>> host.domain.start('trusty')
    (True, 'Domain trusty started', '')

    >>> host.list_domains()
    {'trusty': {'id': 2, 'state': 'running'}}


Snapshots
=========
.. code::

    >>> host.snapshot.create_as('trusty')
    (True, 'Domain snapshot 1453929671 created', '')

    >>> host.snapshot.info('trusty', '1453929671')
    {'children': 0,
     'current': True,
     'descendants': 0,
     'domain': 'trusty',
     'location': 'internal',
     'metadata': True,
     'name': 1453929671,
     'parent': '-',
     'state': 'running'}

    >>> host.snapshot.create_as('trusty')
    (True, 'Domain snapshot 1453929756 created', '')

    >>> host.snapshot.info('trusty', '1453929671')
    {'children': 1,
     'current': False,
     'descendants': 1,
     'domain': 'trusty',
     'location': 'internal',
     'metadata': True,
     'name': 1453929671,
     'parent': '-',
     'state': 'running'}

    >>> host.snapshot.info('trusty', '1453929756')
    {'children': 0,
     'current': True,
     'descendants': 0,
     'domain': 'trusty',
     'location': 'internal',
     'metadata': True,
     'name': 1453929756,
     'parent': 1453929671,
     'state': 'running'}

    >>> kvm.pprint(host.snapshot.conf('trusty', '1453929756'))
    {'creationTime': '1453929756',
     'disks': {'disk': {'@name': 'vda', '@snapshot': 'internal'}},
     'domain': {'@type': 'kvm',
      'clock': {'@offset': 'utc'},
      'currentMemory': {'#text': '2097152', '@unit': 'KiB'},
      'devices': {'console': {'@type': 'pty',
        'target': {'@port': '0', '@type': 'serial'}},
       'controller': [{'@index': '0', '@type': 'usb'},
        {'@index': '0', '@model': 'pci-root', '@type': 'pci'}],
       'disk': {'@device': 'disk',
        '@type': 'volume',
        'address': {'@bus': '0x00',
         '@domain': '0x0000',
         '@function': '0x0',
         '@slot': '0x04',
         '@type': 'pci'},
        'driver': {'@name': 'qemu', '@type': 'qcow2'},
        'source': {'@pool': 'default', '@volume': 'trusty.qcow2'},
        'target': {'@bus': 'virtio', '@dev': 'vda'}},
       'emulator': '/usr/bin/kvm',
       'graphics': {'@autoport': 'yes',
        '@keymap': 'fr',
        '@listen': '127.0.0.1',
        '@port': '-1',
        '@type': 'vnc',
        'listen': {'@address': '127.0.0.1', '@type': 'address'}},
       'input': [{'@bus': 'ps2', '@type': 'mouse'},
        {'@bus': 'ps2', '@type': 'keyboard'}],
       'interface': {'@type': 'network',
        'address': {'@bus': '0x00',
         '@domain': '0x0000',
         '@function': '0x0',
         '@slot': '0x03',
         '@type': 'pci'},
        'mac': {'@address': '54:52:00:cc:ba:4a'},
        'model': {'@type': 'virtio'},
        'source': {'@network': 'br0'}},
       'memballoon': {'@model': 'virtio',
        'address': {'@bus': '0x00',
         '@domain': '0x0000',
         '@function': '0x0',
         '@slot': '0x05',
         '@type': 'pci'}},
       'serial': {'@type': 'pty', 'target': {'@port': '0'}},
       'video': {'address': {'@bus': '0x00',
         '@domain': '0x0000',
         '@function': '0x0',
         '@slot': '0x02',
         '@type': 'pci'},
        'model': {'@heads': '1', '@type': 'cirrus', '@vram': '16384'}}},
      'features': {'acpi': True, 'apic': True, 'pae': True},
      'memory': {'#text': '2097152', '@unit': 'KiB'},
      'name': 'trusty',
      'on_crash': 'restart',
      'on_poweroff': 'destroy',
      'on_reboot': 'restart',
      'os': {'boot': {'@dev': 'hd'},
       'bootmenu': {'@enable': 'no'},
       'type': {'#text': 'hvm', '@arch': 'x86_64', '@machine': 'pc-i440fx-2.3'}},
      'resource': {'partition': '/machine'},
      'title': 'Ubuntu 14.04',
      'uuid': 'e486003f-9f11-f7df-5ed4-cceddbf087ab',
      'vcpu': {'#text': '2', '@placement': 'static'}},
     'memory': {'@snapshot': 'internal'},
     'name': '1453929756',
     'parent': {'name': '1453929671'},
     'state': 'running'}
