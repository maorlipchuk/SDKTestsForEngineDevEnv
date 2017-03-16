import logging

import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import time
import unittest

logging.basicConfig(level=logging.INFO, filename='example.log')
log = logging.getLogger()

# Create a connection to the server:
vm_id='f01048e6-208a-42f3-b2ff-e6f6ac1d5a5a'
disk_id = 'd83a1d61-088c-4423-9695-a752561091b9'
vm_id2='1dc50106-8174-4225-83c6-5318d6a27d90'
disk_id2 = 'a82bfd38-f451-48df-a0d9-f33a1b896330'

connection = sdk.Connection(
    url='http://127.0.0.1:8080/ovirt-engine/api',
    username='admin@internal',
    password='1',
    debug=True,
    log=logging.getLogger(),
)


# Get the reference to the "vms" and "disks" service:
vms_service = connection.system_service().vms_service()

# Find the virtual machine:
vm_search_str = 'id=' + vm_id
vm = vms_service.list(search=vm_search_str)[0]

# Locate the service that manages the virtual machine:
vm_service = vms_service.vm_service(vm.id)

# Locate the service that manages the disk attachments of the virtual
# machine:
disk_attachments_service = vm_service.disk_attachments_service()

class update_disk(unittest.TestCase):
    def __init__(self):
        log.info("Initialize disk")
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        
        # Retrieve the list of disks attachments, and log.info the disk details.
        # Note that each attachment contains a link to the corresponding disk,
        # but not the actual disk data. In order to retrieve the actual disk
        # data we use the `follow_link` method.
        disk = disk_attachments_service.attachment_service(disk_id)
        disk_attachment = disk.update(
            types.DiskAttachment(
                disk=types.Disk(
                    name='mydisk_alias',
                    description='description',
                    qcow_version=types.QcowVersion.QCOW2_V2,
                ),
            ),
        )
        self._wait_for_ok(disk_attachment)
        
    ###############
    #### Tests ####
    ###############
    def testUpdateQcowVersionDiskAliasDesc(self):
        log.info("Test - Update alias description and QCOW version")
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        disk = disk_attachments_service.attachment_service(disk_id)
        disk_attachment = disk.update(
            types.DiskAttachment(
                disk=types.Disk(
                    name='mydisk_new_alias',
                    description='new_description',
                    qcow_version=types.QcowVersion.QCOW2_V3,
                ),
            ),
        )
        self._wait_for_ok(disk_attachment)
        self.validateAliasDescQCOW(old_info=info)

    def validateAliasDescQCOW(self, old_info):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()

        log.info("name: %s" % info.name)
        log.info("id: %s" % info.id)
        log.info("qcow version: %s" % info._qcow_version)
        log.info("provisioned_size: %s" % info.provisioned_size)
        self.assertTrue(info.name != old_info.name)
        self.assertTrue(old_info._qcow_version == types.QcowVersion.QCOW2_V2)
        self.assertTrue(info._qcow_version == types.QcowVersion.QCOW2_V3)
        self.assertTrue(info.description != old_info.description)
        log.info("test result - success")


    #### Test update QCOW ####
    def testUpdateQCOW(self):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("")
        log.info("Test: Update QCOW version")
        log.info("previous qcow version: %s" % info._qcow_version)
        disk = disk_attachments_service.attachment_service(disk_id)
        try:
            disk_attachment = disk.update(
                types.DiskAttachment(
                    disk=types.Disk(
                        qcow_version=types.QcowVersion.QCOW2_V2
                    ),
                ),
            )
        except Exception as e:
            log.error(e)

        self._wait_for_ok(disk_attachment)
        self.validateQCOW(old_info=info)

    def validateQCOW(self, old_info):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()

        log.info("name: %s" % info.name)
        log.info("id: %s" % info.id)
        log.info("old qcow version: %s" % old_info._qcow_version)
        log.info("new qcow version: %s" % info._qcow_version)
        log.info("provisioned_size: %s" % info.provisioned_size)
        self.assertTrue(old_info._qcow_version == types.QcowVersion.QCOW2_V3)
        self.assertTrue(info._qcow_version == types.QcowVersion.QCOW2_V2)
        log.info("test result - success")


    #### Test update alias ####
    def testUpdateAlias(self):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("")
        log.info("Update disk alias and desc")
        log.info("previous disk alias: %s; target disk alias: %s" % (info.name, "my_new_alias"))
        new_alias = 'my_new_alias'
        disk = disk_attachments_service.attachment_service(disk_id)
        disk_attachment = disk.update(
            types.DiskAttachment(
                disk=types.Disk(
                    name=new_alias
                ),
            ),
        )
        self._wait_for_ok(disk_attachment)
        self.validateAlias(new_alias, old_info=info)

    def validateAlias(self, new_alias, old_info):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()

        log.info("new disk alias: %s" % info.name)
        self.assertTrue(old_info.name != info.name)
        self.assertTrue(info.name == new_alias)
        log.info("test result - success")


    #### Test extend size ####
    def testExtendSize(self):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("")
        log.info("Test extend size")
        log.info("previous size: %s" % info.provisioned_size)
        disk = disk_attachments_service.attachment_service(disk_id)
        disk_attachment = disk.update(
            types.DiskAttachment(
                disk=types.Disk(
                    provisioned_size=info.provisioned_size*5/4
                ),
            ),
        )

        self._wait_for_ok(disk_attachment)
        self.validateExtendSize(old_info=info)

        
    def validateExtendSize(self, old_info):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("new size= %s" % info.provisioned_size)
        self.assertTrue(info.provisioned_size == old_info.provisioned_size * 5/4)

    #### Test extend size and compat ####
    def testExtendAndCompat(self):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("")
        log.info("Extend size and update QCOW version")
        log.info("previous size: %s; target size: %s" % (info.provisioned_size, info.provisioned_size*5/4))
        log.info("previous qcow version: %s" % info._qcow_version)
 
        try:
            disk = disk_attachments_service.attachment_service(disk_id)
            disk_attachment = disk.update(
                types.DiskAttachment(
                    disk=types.Disk(
                        qcow_version=types.QcowVersion.QCOW2_V3,
                        provisioned_size=info.provisioned_size*5/4
                    ),
                ),
            )
        except Exception as e:
            log.error(e)
        self._wait_for_ok(disk_attachment)
        self.validateExtendSizeAndCompat(old_info=info)

        
    def validateExtendSizeAndCompat(self, old_info):
        disks_service = connection.system_service().disks_service()
        info = disks_service.disk_service(disk_id).get()
        log.info("new size: %s" % info.provisioned_size)
        log.info("new qcow version: %s" % info._qcow_version)
        self.assertTrue(info.provisioned_size == old_info.provisioned_size * 5/4)
        self.assertTrue(old_info._qcow_version == types.QcowVersion.QCOW2_V2)
        self.assertTrue(info._qcow_version == types.QcowVersion.QCOW2_V3)
 
    def _wait_for_ok(self, disk_attachment):
        # Wait till the disk is OK:
        disks_service = connection.system_service().disks_service()
        disk_service = disks_service.disk_service(disk_attachment.disk.id)
        while True:
            time.sleep(5)
            out = disk_service.get()
            if out.status == types.DiskStatus.OK:
                break

# init disk
log.info("#################################################")
log.info("#### Start test functionality of update disk ####")
log.info("#################################################")
log.info("")
disk = update_disk()

# run tests
disk.testUpdateQcowVersionDiskAliasDesc()
disk.testUpdateQCOW()
disk.testUpdateAlias()
disk.testExtendSize()
disk.testExtendAndCompat()

# Close the connection to the server:
connection.close()

log.info("##################################################")
log.info("#### Finish test functionality of update disk ####")
log.info("##################################################")

