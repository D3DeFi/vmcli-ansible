#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_objectlist_info
short_description: Provides listing of objects of specified type
description:
  - Provides listing of object names based on VMware type provided by user
  - Other details about objects are not retrieved and are considered unnecessary
  - If any other details are required, user is expected to use official ansible vmware modules
  - List of VMware objects is not tied to specific datacenter as is the case with official vmware modules from upstream
version_added: 2.9
author:
  - Dusan Matejka (@D3DeFi)
notes:
  - Tested on vSphere 6.5
requirements:
  - python >= 2.6
  - PyVmomi
options:
  type:
    description:
      - type of objects to list
      - if I(type=datastore) both datastore and datastore clusters are returned
      - if I(type=network) both portgroups and DVS portgroups are returned
      - on I(type=folder) listing is returned with absolute paths as expected by vmware_guest module
      - only vm folders are retrieved and network, host or datastore folders are skipped when I(type=folder)
    required: true
    type: str
    choices: [virtual_machine, datacenter, folder, cluster, datastore, resource_pool, network]
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Provide information about vCenter folders
  vmware_objectlist_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    type: datastore
  delegate_to: localhost
  register: vcenter_datastore_list
'''

RETURN = r'''
virtual_machine_info:
  description:
    - list of virtual machine names
  returned: on success when type=virtual_machine
  sample:
    [
      'exampleHost01',
      'db02'
    ]
datacenter_info:
  description:
    - list of datacenter names
  returned: on success when type=datacenter
  sample:
    [
      'DC01',
      'DC02'
    ]
folder_info:
  description:
    - list of vm absolute paths
  returned: on success when type=folder
  sample:
    [
      '/deparment/team1/test_vms',
      '/prod/web01/db_vms'
    ]
cluster_info:
  description:
    - list of cluster names
  returned: on success when type=cluster
  sample:
    [
      'cl01',
      'cl02'
    ]
datastore_info:
  description:
    - list of datastore dictionaries with names and types
  returned: on success when type=datastore
  sample:
    [
      {
        name: 'ds01',
        type: 'datastore'
      },
      {
        name: 'dscl01',
        type: 'datastore_cluster'
      }
    ]
resource_pool_info:
  description:
    - list of resource pool names
  returned: on success when type=resource_pool
  sample:
    [
      'rp01',
      'secretTeam'
    ]
network_info:
  description:
    - list of network names
  returned: on success when type=network
  sample:
    [
      'VLAN01',
      'VLAN02'
    ]
'''


try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, get_all_objs


VMWARE_TYPES = {
    'virtual_machine': [vim.VirtualMachine],
    'datacenter': [vim.Datacenter],
    'folder': [vim.Folder],
    'cluster': [vim.ClusterComputeResource],
    'datastore': [vim.Datastore, vim.StoragePod],
    'resource_pool': [vim.ResourcePool],
    'network': [vim.Network, vim.dvs.DistributedVirtualPortgroup],
}


class PyVmomiObjListings(PyVmomi):
    def __init__(self, module):
        super(PyVmomiObjListings, self).__init__(module)

    def get_listing(self, objtype):
        """retrieves simple list of object names per object type

        Returns:
            list of dictionaries holding object names
        """
        objtype_name = str(objtype) + '_info'
        result = {objtype_name: []}
        objects = get_all_objs(self.content, VMWARE_TYPES[objtype])
        for obj in list(objects):
            result[objtype_name].append(str(obj.name.encode('utf-8')))

        result[objtype_name] = sorted(result[objtype_name])
        return result

    def get_folder_listing(self):
        """retrieves list of folders with their names and absolute paths

        Returns:
            list of dictionaries, where each dictionary represent folder and
            contains name and abolute path to the folder
        """
        result = {'folder_info': []}
        objects = get_all_objs(self.content, VMWARE_TYPES['folder'])
        for folder in list(objects):
            # filter root folders for each type and discard folders that cannot hold VMs
            if folder.name in ['vm', 'network', 'datastore', 'host'] or 'VirtualMachine' not in folder.childType:
                continue

            result['folder_info'].append(self.compose_absolute_path(folder))

        result['folder_info'] = sorted(result['folder_info'])
        return result

    def compose_absolute_path(self, folder, path=None):
        """composes absolute path to the folder by traversing parents until root folder is found

        Args:
            folder: vim.Folder object
            path: so far composed path
        Returns:
            absolute path to the folder with the folder included
        """
        # do recursion until folder is None or folder with 'vm' name is found
        if folder is not None:
            # break recursion if folder name is 'vm' as we are not interested in going deeper
            if folder.name == 'vm':
                return '/' + str(path)

            # define folder itself as a path if recursion is only starting
            if not path or path is None:
                path = str(folder.name.encode('utf-8'))
            else:
                # prepend current folder to the path obtained so far
                path = '{}/{}'.format(folder.name.encode('utf-8'), path)

            # continue recursion if folder has a parent folder
            if folder.parent is not None:
                return self.compose_absolute_path(folder.parent, path)

        return path

    def get_datastore_listing(self):
        """retrieves list of datastore names and types

        Returns:
            list of dictionaries holding datastore names and types
        """
        result = {'datastore_info': []}
        objects = get_all_objs(self.content, VMWARE_TYPES['datastore'])
        for obj in list(objects):
            if isinstance(obj, vim.StoragePod):
                dstype = 'datastore_cluster'
            elif isinstance(obj, vim.Datastore):
                dstype = 'datastore'

            result['datastore_info'].append({'type': dstype, 'name': obj.name})

        result['datastore_info'] = sorted(result['datastore_info'], key=lambda k: k['type'] + k['name'])
        return result



def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        type=dict(type='str', choices=list(VMWARE_TYPES.keys()), required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec)
    pyv = PyVmomiObjListings(module)

    if module.params['type'] == 'folder':
        listing = pyv.get_folder_listing()
    elif module.params['type'] == 'datastore':
        listing = pyv.get_datastore_listing()
    else:
        listing = pyv.get_listing(module.params['type'])

    module.exit_json(result=listing, ok=True)

if __name__ == '__main__':
    main()
