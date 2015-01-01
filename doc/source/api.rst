***
API
***


Constants
=========

.. attribute:: CONTROLS

``unix`` module possess controls for manipulating some behaviours (like if
options are put before or after arguments, how to decode outputs, ...). These
controls are in fact private attributes of the object. Controls of this module
are:

  * **parse**: indicate whether the result of a command is parsed. The value of
    ``stdout`` is splited in lines and returned or the **KvmError** exception is
    raised.


Methods
=======

.. method:: gen_uuid()

Generate a random uuid.

.. method:: gen_mac()

Generate a random mac address.

.. method:: _xml_to_dict(elt)

Recursive function that transform an XML element to a dictionnary.
**elt** must be of type ``lxml.etree.Element``.


Exceptions
==========
.. class:: KvmError

Main exception for this module.


Hypervisor object
=================

.. class:: Hypervisor(host)

This object represent an Hypervisor. **host** must be an object of
type ``unix.Local`` or ``unix.Remote`` (or an object inheriting from
them).

.. note::

   In the following documentation, an Hypervisor is represented by the
   ``hypervisor`` keyword.

   ``hypervisor.generic.capabilities`` is the method ``capabilities`` of the
   object returned by the ``generic`` property of an ``Hypervisor`` instance.

.. method:: hypervisor.virsh(command, *args, **kwargs)

Wrap the execution of the virsh command. It set a control for
putting options after the virsh **command**. If **parse** control
is activated, the value of ``stdout`` is returned or **KvmError**
exception is raised.

Generic commands
----------------

.. method:: hypervisor.generic.capabilities(self)

Return a dictionnary (generated from XML) describing the
capabilities of the hypervisor we are currently connected to. This
includes a section on the host capabilities in terms of CPU and
features, and a set of description for each kind of guest which can be
virtualized. For a more complete description see:
http://libvirt.org/formatcaps.html.


.. method:: hypervisor.generic.domcapabilities(self, *args)

Return a dictionnary (generated from XML) describing the domain
capabilities for the hypervisor we are connected to using information
either sourced from an existing domain or taken from the virsh
capabilities output.


.. method:: hypervisor.generic.freecell(self, **kwargs)

Prints the available amount of memory on the machine or within a NUMA
cell.


.. method:: hypervisor.generic.node_memory_tune(self, *args)

Allows you to display or set the node memory parameters. ***args**
can have at most three elements: *shm-pages-to-scan*,
*shm-sleep-millisecs* and *shm-merge-across-nodes*. *shm-pages-to-scan*
can be used to set the number of pages to scan before the shared memory
service goes to sleep; *shm-sleep-millisecs* can be used to set the
number of millisecs the shared memory service should sleep before next
scan; *shm-merge-across-nodes* specifies if pages from different numa
nodes can be merged. When set to 0, only pages which physically reside
in the memory area of same NUMA node can be merged. When set to 1, pages
from all nodes can be merged. Default to 1.

Note: Currently the "shared memory service" only means KSM (Kernel
Samepage Merging).


.. method:: hypervisor.generic.nodecpumap(self)

Displays the node's total number of CPUs, the number of online CPUs
and the list of online CPUs.


.. method:: hypervisor.generic.nodecpustats(self, cpu='*', percent=False)

Returns cpu stats of the node. If **cpu** is specified, this will
prints specified cpu statistics only. If **percent** is specified,
this will prints percentage of each kind of cpu statistics during 1
second.


.. method:: hypervisor.generic.nodeinfo(self)

Returns basic information about the node, like number and type of
CPU, and size of the physical memory.


.. method:: hypervisor.generic.nodememstats(self, cell='*')

Returns memory stats of the node. If **cell** is specified, this
will prints specified cell statistics only.


.. method:: hypervisor.generic.nodesuspend(self, target, duration)

Puts the hypervisor into a system-wide sleep state and schedule the
node's Real-Time-Clock interrupt to resume the node after the time
duration specified by **duration** is out. **target** specifies the
state to which the host will be suspended to, it can be *mem* (suspend
to RAM), *disk* (suspend to disk), or *hybrid* (suspend to both RAM and
disk). **duration** specifies the time duration in seconds for which the
host has to be suspended, it should be at least 60 seconds.


.. method:: hypervisor.generic.sysinfo(self)

Print the representation of the hypervisor sysinfo, if available.


.. method:: hypervisor.generic.version(self)

Will print out the major version info about what this built from.


