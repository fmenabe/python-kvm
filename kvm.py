"""This module allow to manage KVM hosts."""

import os
import re
import random
import string
import unix

import sys
SELF = sys.modules[__name__]


# Controls.
CONTROLS = {'parse': False}
unix.CONTROLS.update(CONTROLS)

# Characters in generating strings.
_CHOICES = string.ascii_letters[:6] + string.digits


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


#
# Exceptions
#
class KvmError(Exception):
    """Main exception for this module."""
    pass


#
## Classes.
#
def Hypervisor(host):
    unix.isvalid(host)

    class Hypervisor(host.__class__):
        """This object represent an Hypervisor. **host** must be an object of
        type ``unix.Local`` or ``unix.Remote`` (or an object inheriting from
        them).
        """
        def __init__(self):
            host.__class__.__init__(self)
            self.__dict__.update(host.__dict__)
            for control, value in iteritems(CONTROLS):
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
                if not self._parse:
                    return status, stdout, stderr
                elif not status:
                    raise KvmError(stderr)
                else:
                    return stdout.splitlines()[:-1]

    return Hypervisor()
