The purpose of this module is to manage KVM hosts (starting/stopping/destroying VM, createing/resizing disks, ...). It is just the definition of many basic commands of 'virsh' and 'qemu'. It use the module 'python-unix' and class decorators for flexibility and simplicity.

Better explications are examples ^^:

  >>> import unix
  >>> import kvm
  >>> # KVM on localhost
  >>> kvm_host = kvm.KVM(unix.Local())
  >>> kvm_host.vms
  >>>   ['vm1', 'vm2']
  >>> kvm_hosts.state('vm1')
  >>>   'running'
  >>> kvm_host.stop('vm1')
  >>> # Wait a few seconds for the VM to stop.
  >>> kvm_host.state('vm1')
  >>>  'shut off'
  >>> ...
  >>>
  >>> # KVM on a remote host
  >>> kvm_host = kvm.KVM(unix.Remote())
  >>> kvm_host.connect('192.168.1.1')
  >>> kvm_host.vms
  >>> ['vm10', 'vm11']
  >>> kvm_host.state('vm10')
  >>>  'shut off'
  >>> kvm_host.start('vm10')
  >>> # After the VM has started (depend of the OS)
  >>> kvm_host.state('vm10')
  >>>  'running'
  >>> ...
