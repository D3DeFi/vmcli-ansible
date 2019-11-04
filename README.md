vmcli-ansible
=============

This repository is an attempt to move some of the [vmcli](https://github.com/D3DeFi/vmcli) functionality into ansible
as vmware modules in ansible have been improved rapidly in the past years. This should be considered only as a preview,
but can be made working in your environment with little effort. Read below.

This project is intended to provide a generalized tool for simple VMware operations like creating VM and forgetting
about it. More serious projects should have their whole server lifecycle automated in a more customized way unique
to the project itself. Consider this for use cases where you need to spawn different VMs with different OSes every few
days or so.

It aims to not burden user with a lot of customization directives and tries to fill in some of the values for the
user from (administrator) predefined defaults.

Installation
------------

Ansible is expected to be installed on your controller machine as well as vmware libraries for python:

    pip install -r requirements.txt

A few things have been implemented to ease the decision process for the user. If you plan to use this only by yourself
then you can replace variables in `vars/vcenter-logins.yml` with your credentials.

By default, vmcli-ansible tries to load default datacenter and cluster for specific vCenter in task file
`tasks/validate-inputs.yml`, which retrieves it from static definition present in `group_vars/all.yml`.
Make sure to edit these files and add more default values (e.g. datastore, rpool) as desired.

Next is the required `guest_id` that should match OS installed on the VM template. As this is usually something that I
consider duplicate with the template option, matching guest ids are loaded from `roles/vmware_vm/vars/main.yml` and
should be configured only once before using this project.

Static IP addressing is assumed by default. This is loaded from VM extra config as guest os customizations doesn't
support some distributions. Role `vmware_vm` configures the following directives in the VM extra config during its creation:

    guestinfo.provision.enabled: true
    guestinfo.provision.network.address: '{{ vmware_vm_ip_cidr }}'
    guestinfo.provision.network.gateway: '{{ vmware_vm_ip_gw }}'

If this feature is not required,`guestinfo.provision.enabled` should simply be set to `false` or whole extra config
should be completely removed from `roles/vmware_vm/tasks/main.yml` file.

In order to make static IP addressing work, templates should have custom provisioning script present on themselves.
This feature will natively work with [vmcli-provision-scripts](https://github.com/D3DeFi/vmcli-provision-scripts)
or you can develop your own version that suits your needs.

How To
------

Everything deployed will derive from inventory you provide to the playbooks. Start by looking at the inventory.yml
present in this project and consult `roles/vmware_vm/README.md` for any configurable options. Additional groups of
hosts can be created under managed\_vms group. This for example allows user to spawn VMs simultaneously on multiple
vCenters.

Login information is expected to come from one of the following sources:

* ENV variables `VMWARE_HOST`, `VMWARE_USER` and `VMWARE_PASSWORD`
* ansible variables `vcenter_hostname`, `vcenter_username` and `vcenter_password`. These can be defined:
  * in the inventory file itself
  * in the `group_vars/all.yml` file
  * from the command line as an option to `ansible-playbook site.yml -e vcenter_hostname=XYZ`

VMware requires a few options before it can deploy anything, such information can be gathered by running:

    ansible-playbook list.yml --tags datastore -e vcenter_hostname=vcenter01.example.com -e vcenter_username=admin

VMs are deployed running the following command (this example uses ENV variables instead):

    export VMWARE_HOST=vcenter01.example.com
    export VMWARE_USER=admin
    export VMWARE_PASSWORD=mypass
    ansible-playbook site.yml -i inventory.yml

There is also a playbook for VM destroy:

    ansible-playbook destroy.yml -i inventory.yml

Author Information
------------------

Dusan Matejka (@D3DeFi)

