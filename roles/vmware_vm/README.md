vmware\_vm
==========

A collection of tasks, plugins and mappings to ease VMware VM creation for end user.

Requirements
------------

- PyVmomi
- vsphere-automation-sdk-python (if VM tags are going to be used)

Role Variables
--------------

Following is the listing of variables and their default values (if present).

This role expects login information to be set either via ENV variables or from playbook:

    vcenter_hostname:  # or VMWARE_HOST env variable
    vcenter_username:  # or VMWARE_USER env variable
    vcenter_password:  # or VMWARE_PASSWORD env variable
    vcenter_validate_certs: True

Variables configuring VM creation and placement:

    vmware_vm_name: '{{ inventory_hostname }}'
    vmware_vm_template:         # name of template
    vmware_vm_folder:           # absolute path to folder
    vmware_vm_resource_pool:
    vmware_vm_datacenter:
    vmware_vm_cluster:
    vmware_vm_datastore:        # datastore or datastore cluster name

Variables configuring networking for VM:

    vmware_vm_networks: []      # list with `- name: VLAN1` network pairs, see example
    vmware_vm_ip_cidr:          # IP in CIDR format, e.g. 10.1.1.2/24
    vmware_vm_ip_gw:

Additional customization can be made to network interfaces assigned to the VM based on options suported in 'networks' parameter present in vmware\_guest module. See the [documentation](https://docs.ansible.com/ansible/latest/modules/vmware_guest_module.html).

Variables related to VM hardware configuration:

    vmware_vm_cpus: 1
    vmware_vm_memory_mb: 1024
    vmware_vm_scsi_type: paravirtual
    vmware_vm_add_disks: []     # list with a minimum of `- size_gb: 123` pairs, see example

Additional disk customization can be made per disk. See the [vmware\_guest\_disk documentation](https://docs.ansible.com/ansible/latest/modules/vmware_guest_disk_module.html) for all available options.

List of disks is passed through custom filter `to_vmware_disks` plugin that tries to fill in every required defaults for user's convenience. If `datastore` or `datastore_cluster` is missing, plugin defaults to datastore VM was created on. If `scsi_controller` or `unit_number` is missing, plugin tries to assign them automatically starting with scsi controller 0:3 unit\_number as a sane defaults. However, this can be overriden via plugin arguments.

Assigning tags to VM is handled by different python library (vsphere-automation-sdk-python):

    vmware_vm_tags: []          # a list of tags to assign, see example

By default this module will fail if VM with the same name is already found on vCenter. This can be overriden, but the destination VM will be powered off and reconfigured if done:

    vmware_vm_update_existing: False

Example Playbook
----------------

```yaml
- hosts: managed_vms
  vars:
    vcenter_hostname: vcenter01.example.com
    vcenter_username: admin
    vcenter_password: password
  roles:
    - role: vmware_vm
      vmware_vm_name: example01
      vmware_vm_template: centos7-template
      vmware_vm_datastore: exampleDScluster01
      vmware_vm_datacenter: datacenter01
      vmware_vm_networks:
        - name: VLAN1
      vmware_vm_ip_cidr: 10.1.1.2/24
      vmware_vm_ip_gw: 10.1.1.1
      vmware_vm_add_disks:
        - size_gb: 100
        - size_tb: 2
          datastore: BigDS
      vmware_vm_tags:
        - MyTag1
```

Author Information
------------------

Dusan Matejka (@D3DeFi)
