********
Overview
********

This module aims to manage KVM hypervisors. For this it use the
`unix module <https://github.com/fmenabe/python-unix>`_ which allow to manage
Unix-like systems, both locally and remotely, in the same by overloading class
instances. This module is just a wrapper to the ``virsh`` command. It parse
outputs of ``virsh command`` (both XML and text). Commands are grouped in childs
objects accessible via properties.


Installation
============
This module is compatible with python2.7 and python 3.*. The module is
on **PyPi** so you can use the ``pip`` command for installing it.

For example, to use ``kvm`` in a virtualenv:

.. code:: bash

   $ virtualenv env/ --prompt "(myprog)"
   $ . ./env/bin/activate
   (myprog) $ pip install kvm

Otherwise sources are on github: https://github.com/fmenabe/python-kvm

Usage
=====
You need to import the necessary classes from ``unix`` module. An hypervisor is
represented by the **Hypervisor** class and must wrap an object of type
``unix.Local`` or ``unix.Remote``. It theorically support any Unix system, but
disks manipulations need *nbd* module to be loaded so it is better to use an
``unix.linux.Linux`` host.

.. code-block:: python

    >>> from unix import Local, Remote, UnixError
    >>> from unix.linux import Linux
    >>> import kvm
    >>> localhost = kvm.Hypervisor(Linux(Local()))
    >>> localhost.generic.nodeinfo()
    {'nb_cpu': 1,
     'nb_threads_per_core': 2,
     'memory': 16331936,
     'numa_cells': 1,
     'cpu_model': 'x86_64',
     'nb_cores_per_cpu': 4,
     'nb_cores': 8,
     'cpu_freq': 1340}
