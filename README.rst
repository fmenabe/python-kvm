python-kvm
==========

This module aims to manage KVM hypervisors. For this it use the
`unix module <https://github.com/fmenabe/python-unix>`_ which allow to manage
Unix-like systems, both locally and remotely, in the same by overloading class
instances. This module is just a wrapper to the ``virsh`` command. It parse
outputs of the ``virsh`` command (both XML and text). Commands are grouped in
childs objects accessible via properties.

Installation
------------
This module is compatible with python2.7 and python 3.*. The module is
on **PyPi** so you can use the ``pip`` command for installing it.

For example, to use ``kvm`` in a virtualenv:

.. code:: bash

   $ virtualenv env/ --prompt "(myprog)"
   $ . ./env/bin/activate
   (myprog) $ pip install kvm

Otherwise sources are on github: https://github.com/fmenabe/python-kvm

Usage
-----
You need to import the necessary classes from ``unix`` module. An hypervisor is
represented by the **Hypervisor** object and must wrap an object of type
``unix.Local`` or ``unix.Remote``. It theorically support any Unix system, but
disks manipulations need *nbd* module to be loaded so it is better to use an
``unix.linux.Linux`` host.

.. code-block:: python

    >>> from unix import Local, Remote, UnixError
    >>> from unix.linux import Linux
    >>> import kvm
    >>> import json
    >>> localhost = kvm.Hypervisor(Linux(Local()))
    >>> localhost.hypervisor.nodeinfo()
    {'nb_cpu': 1,
     'nb_threads_per_core': 2,
     'memory': 16331936,
     'numa_cells': 1,
     'cpu_model': 'x86_64',
     'nb_cores_per_cpu': 4,
     'nb_cores': 8,
     'cpu_freq': 1340}
    >>> localhost.list_domains(all=True)
    {'guest1': {'id': -1, 'state': 'shut off'}}
    {'guest2': {'id': 1, 'state': 'running'}}
    >>> localhost.domain.start('guest1')
    # Wait a few seconds for the domain to start.
    >>> localhost.domain.state('guest1')
    'running'
    >>> localhost.domain.id('guest1')
    2
    >>> print(json.dumps(localhost.domain.conf('guest1'), indent=2))
    # json is use for pretty printing the dictionnary containing the
    # configuration.
    {
      "@type": "kvm",
      "name": "guest1",
      "uuid": "ed68d942-5d4b-7bba-4d74-7d44d73779d3",
      "memory": {
        "@unit": "KiB",
        "#text": "2097152"
      },
      ...
    }
    >>> localhost.list_networks()
    {'default': {'autostart': True, 'persistent': True, 'state': 'active'}}

    >>> host = Remote()
    >>> host.connect('hypervisor1')
    >>> host = kvm.Hypervisor(Linux(host))
    >>> host.hypervisor.nodeinfo()
    {'cores_per_socket': 12,
     'cpu_frequency': '2200 MHz',
     'cpu_model': 'x86_64',
     'cpu_sockets': 2,
     'cpus': 24,
     'memory_size': '98974432 kB',
     'numa_cells': 1,
     'threads_per_core': 1}
    >>> host.list_domains(all=True)
    {'guest1': {'id': 1, 'state': 'running'}}
    {'guest2': {'id': 2, 'state': 'running'}}
    >>> host.domain.shutdown('guest2')
    # Wait for the domain to stop.
    >>> host.domain.state('guest1')
    'shut off'

    # Using the context manager for the connecion.
    >>> from unix.linux as linux, kvm
    >>> with linux.connect('hypervisor1') as host:
    ...   host = kvm.Hypervisor(host)
    ...   host.hypervisor.node_info()
