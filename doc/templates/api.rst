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

.. method:: {{ gen_uuid.signature }}

{{ gen_uuid.doc }}

.. method:: {{ gen_mac.signature }}

{{ gen_mac.doc }}

.. method:: {{ _xml_to_dict.signature }}

{{ _xml_to_dict.doc }}


Exceptions
==========
.. class:: KvmError

{{ KvmError }}


Hypervisor object
=================

.. class:: Hypervisor(host)

{{ hypervisor.doc }}

.. note::

   In the following documentation, an Hypervisor is represented by the
   ``hypervisor`` keyword.

   ``hypervisor.generic.capabilities`` is the method ``capabilities`` of the
   object returned by the ``generic`` property of an ``Hypervisor`` instance.

.. method:: {{ hypervisor.virsh.signature }}

{{ hypervisor.virsh.doc }}

Generic commands
----------------
{% for method in hypervisor.childs.generic %}
.. method:: {{ method.signature }}

{{ method.doc }}

{% endfor %}
