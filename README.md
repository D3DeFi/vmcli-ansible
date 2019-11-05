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

Ansible is expected to be installed on your controller machine. Install required VMware libraries for python with:

    pip install -r requirements.txt


Additional customization
------------------------

As `vmware_guest` module requires some options to be filled before spawning any VM. A few things have been
implemented to ease the decision process for the end user by defaulting to the most common values
(e.g. a smaller vCenter setup run with a single datacenter).

### Default values

An attempt is made to load default datacenter and cluster for vCenter you are targeting. These default
values, however, needs to be configured for the first time manually in:

    tasks/validate-inputs.yml   # task file responsible for loading default values
    group_vars/all.yml          # static definition of default values, add more as desired

You are encouraged to define additional default values (e.g. datastore, rpool) if possible for your setup or remove
any existing ones from those files.

### Parameter guest\_id is required

Next is the required `guest_id` that should match OS installed on the VM template. This information usually changes
with the template itself, which should not be that often, thus a static mapping of template <-> guest\_id is kept
in the vmware\_vm role itself and it should be adjusted by the user when setting up this repository:

	roles/vmware_vm/vars/main.yml

### Static IP addressing

Static IP addressing is assumed by default as it is harder to provision VM with when compared to DHCP. Configuration
is not achieved via vmtools guest os customizations feature due to the fact that VMware doesn't support all popular
distributions.

Instead, a few variables are written to VM's extra config, which are then loaded via first boot provisioning script
enabled inside the template. This feature will natively work with
[vmcli-provision-scripts](https://github.com/D3DeFi/vmcli-provision-scripts)
or you can develop your own version that suits your needs.

Role `vmware_vm` configures the following directives in the VM extra config during its creation:

    guestinfo.provision.enabled: true
    guestinfo.provision.network.address: '{{ vmware_vm_ip_cidr }}'
    guestinfo.provision.network.gateway: '{{ vmware_vm_ip_gw }}'

If this feature is not required, `guestinfo.provision.enabled` should simply be set to `false` or whole extra config
should be completely removed from `roles/vmware_vm/tasks/main.yml` file.


How To
------

Everything deployed will derive from inventory you provide to the playbooks. Start by looking at the `inventory.yml`
present in this project and then consult `roles/vmware_vm/README.md` for any additional configurable options.
More groups of hosts can be created under managed\_vms group. This for example allows user to spawn VMs simultaneously
on multiple vCenters.

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

