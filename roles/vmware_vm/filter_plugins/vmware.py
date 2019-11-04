#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Custom filters to help with data transition between user and ansible vmware modules
#


from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native


class FilterModule(object):

    def filters(self):
        return {
            'to_vmware_disks': self.to_vmware_disks
        }

    def to_vmware_disks(self, disks, datastore=None, disktype='thin', scsi_controller=0, unit_number=3):
        """Converts disks to format required by vmware_guest_disk module

        vmware_guest_disk ansible module requires a few specific options to be
        present when adding a new disk to VM. This method, representing Ansible
        filter plugin, allows user to specify only some of them and fills the
        rest into an expected format. It only supports assignements to a single
        SCSI controller.

        Use in playbooks as follows:
            '{{ simple_disk_list|to_vmware_disks(datastore="MyDatastore") }}'

        Args:
            disks: list of key-value pairs in format [{'size_gb': N}]
            datastore: name of vCenter datastore where to save disk files
            disktype: type of a disk used for creation ('thin', 'thick', etc..)
            scsi_controller: integer identifying VM SCSI controller to which
                disks should be attached
            unit_number: integer with minimal allowed unit number that should
                be used on SCSI controller for the disks. First numbers are
                usually used for OS disks

        Returns:
            A list of dictionaries containing required parameters for
            vmware_guest_disk ansible module. Example:

            [
                {
                    'size_gb': 32,
                    'type': 'thin',
                    'datastore': 'TestDatastore',
                    'scsi_controller': 0,
                    'unit_number': 3
                }
            ]
        """
        try:
            # get already assigned unit_numbers
            occupied_unums = [x['unit_number'] for x in disks if 'unit_number' in list(x.keys())]
            # gather list of available unit_numbers starting from minimal allowed value
            if unit_number < 16:
                free_unit_nums = sorted(list({n for n in range(unit_number, 16)} - set(occupied_unums)))
            else:
                raise Exception('assigned unit_number would be bigger than SCSI controller limit of 15')

            # iterate over disks and check which values are missing
            for d in disks:
                # either datastore or autoselect_datastore needs to be present
                if d.get('datastore') is None and d.get('autoselect_datastore') is None:
                    # attempt to load default which was provided to filter as an argument
                    if datastore is not None:
                        d['datastore'] = datastore
                    else:
                        raise Exception('datastore parameter missing in both original data and filter arguments')

                # convert disk to expected disk type
                if d.get('type') is None:
                    d['type'] = disktype

                # assign specific unit_number for disk if not present already
                if d.get('unit_number') is None:
                    # check if there are still free unit numbers for SCSI controller left
                    if len(free_unit_nums) > 0:
                        # assign next free unit_number to disk and increment it
                        d['unit_number'] = free_unit_nums.pop(0)
                    else:
                        raise Exception('No more free unit numbers on SCSI controller left to assign')

                # assign disk to specific scsi_controller if not present already
                if d.get('scsi_controller') is None:
                    # number of SCSI controllers is limited to 4 per VM
                    if scsi_controller < 4:
                        d['scsi_controller'] = scsi_controller
                    else:
                        raise Exception('Number for SCSI controller would exceed VM limit of 4')

        except Exception as e:
            raise AnsibleError('to_vmware_disks filter plugin failed with exception: {}'.format(to_native(e)))

        return disks

