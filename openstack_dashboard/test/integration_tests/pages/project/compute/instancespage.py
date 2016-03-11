#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables
from openstack_dashboard.test.integration_tests.regions import menus


class InstanceForm(forms.VerticalTabbedFormRegion):
    CREATE_INSTANCE_FORM_FIELDS = (({"name": "name",
                                    "availability-zone": "availability-zone",
                                     "count": "count"}),
                                   ({"boot-source-type": "boot-source-type", "image": "image",
                                    "snapshot": "snapshot", "volume": "volume",
                                     "volume-snapshot": "volume_snapshot",
                                     "vol-create": "vol_create",
                                     'boot_sources': menus.TransferTableMenuRegion}),
                                   ({'flavors': menus.TransferTableMenuRegion}),
                                   ({'networks': menus.TransferTableMenuRegion}))

    def __init__(self, driver, conf, tab=0):
        super(InstanceForm, self).__init__\
            (driver, conf, field_mappings=self.CREATE_INSTANCE_FORM_FIELDS)


class InstancesTable(tables.TableRegion):
    name = "instances"
    CREATE_INSTANCE_FORM_FIELDS = ((
        "availability_zone", "name", "flavor",
        "count", "source_type", "instance_snapshot_id",
        "volume_id", "volume_snapshot_id", "image_id", "volume_size",
        "vol_delete_on_instance_delete"),
        ("keypair", "groups"),
        ("script_source", "script_upload", "script_data"),
        ("disk_config", "config_drive")
    )

    @tables.bind_table_action('launch')
    def launch_instance(self, launch_button):
        launch_button.click()
        return forms.TabbedFormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_INSTANCE_FORM_FIELDS)

    @tables.bind_table_action('launch-ng')
    def launch_instancenew(self, launch_button):
        launch_button.click()
        return InstanceForm(
            self.driver, self.conf)

    @tables.bind_table_action('delete')
    def delete_instance(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class InstancesPage(basepage.BaseNavigationPage):

    DEFAULT_FLAVOR = 'm1.tiny'
    DEFAULT_COUNT = 1
    DEFAULT_BOOT_SOURCE = 'Boot from image'
    DEFAULT_VOLUME_NAME = None
    DEFAULT_SNAPSHOT_NAME = None
    DEFAULT_VOLUME_SNAPSHOT_NAME = None
    DEFAULT_VOL_DELETE_ON_INSTANCE_DELETE = False
    DEFAULT_SECURITY_GROUP = True

    INSTANCES_TABLE_NAME_COLUMN = 'name'
    INSTANCES_TABLE_STATUS_COLUMN = 'status'
    INSTANCES_TABLE_IP_COLUMN = 'ip'
    INSTANCES_TABLE_IMAGE_NAME_COLUMN = 'image_name'

    NEW_DEFAULT_AZ = 'nova'
    NEW_DEFAULT_COUNT = 1
    NEW_DEFAULT_BOOT_SOURCE = 'image'
    NEW_DEFAULT_VOLUME_NAME = None
    NEW_DEFAULT_SNAPSHOT_NAME = None
    NEW_DEFAULT_VOLUME_SNAPSHOT_NAME = None
    NEW_DEFAULT_VOLUME_CREATION = 'No'
    NEW_DEFAULT_BOOT_SOURCE_NAME = 'cirros-0.3.4-x86_64-uec'
    NEW_DEFAULT_NETWORK = 'public'
    NEW_DEFAULT_FLAVOR = 'm1.tiny'


    def __init__(self, driver, conf):
        super(InstancesPage, self).__init__(driver, conf)
        self._page_title = "Instances"

    def _get_row_with_instance_name(self, name):
        return self.instances_table.get_row(self.INSTANCES_TABLE_NAME_COLUMN,
                                            name)

    @property
    def instances_table(self):
        return InstancesTable(self.driver, self.conf)

    def is_instance_present(self, name):
        return bool(self._get_row_with_instance_name(name))

    def create_instance(
            self, instance_name,
            available_zone=None,
            instance_count=DEFAULT_COUNT,
            flavor=DEFAULT_FLAVOR,
            boot_source=DEFAULT_BOOT_SOURCE,
            source_name=None,
            device_size=None,
            vol_delete_on_instance_delete=DEFAULT_VOL_DELETE_ON_INSTANCE_DELETE
    ):
        if not available_zone:
            available_zone = self.conf.launch_instances.available_zone
        instance_form = self.instances_table.launch_instance()
        instance_form.availability_zone.value = available_zone
        instance_form.name.text = instance_name
        instance_form.flavor.text = flavor
        instance_form.count.value = instance_count
        instance_form.source_type.text = boot_source
        boot_source = self._get_source_name(instance_form, boot_source,
                                            self.conf.launch_instances)
        if not source_name:
            source_name = boot_source[1]
        boot_source[0].text = source_name
        if device_size:
            instance_form.volume_size.value = device_size
        if vol_delete_on_instance_delete:
            instance_form.vol_delete_on_instance_delete.mark()
        instance_form.submit()

    def launch_instance(self, name, availability_zone=NEW_DEFAULT_AZ,
                        instance_count=NEW_DEFAULT_COUNT,
                        boot_source_type=NEW_DEFAULT_BOOT_SOURCE,
                        image_name=NEW_DEFAULT_BOOT_SOURCE_NAME,
                        create_volume=NEW_DEFAULT_VOLUME_CREATION,
                        flavor_size=DEFAULT_FLAVOR,
                        network=NEW_DEFAULT_NETWORK):

        launch_instance_form = self.instances_table.launch_instancenew()
        launch_instance_form.name.text = name
        launch_instance_form.availability_zone.text = availability_zone
        launch_instance_form.instance_count.text = instance_count
        launch_instance_form.boot_source_type = boot_source_type
        launch_instance_form.create_volume.text = create_volume
        launch_instance_form.boot_sources.allocate_boot_source(name=image_name)
        launch_instance_form.flavors.allocate_flavor(name=flavor_size)
        launch_instance_form.networks.allocate_network(name=network)
        launch_instance_form.submit()

    def delete_instance(self, name):
        row = self._get_row_with_instance_name(name)
        row.mark()
        confirm_delete_instances_form = self.instances_table.delete_instance()
        confirm_delete_instances_form.submit()

    def is_instance_deleted(self, name):
        return self.instances_table.is_row_deleted(
            lambda: self._get_row_with_instance_name(name))

    def is_instance_active(self, name):
        row = self._get_row_with_instance_name(name)
        return self.instances_table.is_cell_status(
            lambda: row.cells[self.INSTANCES_TABLE_STATUS_COLUMN], 'Active')

    def _get_source_name(self, instance, boot_source,
                         conf):
        if 'image' in boot_source:
            return instance.image_id, conf.image_name
        elif boot_source == 'Boot from volume':
            return instance.volume_id, self.DEFAULT_VOLUME_NAME
        elif boot_source == 'Boot from snapshot':
            return instance.instance_snapshot_id, self.DEFAULT_SNAPSHOT_NAME
        elif 'volume snapshot (creates a new volume)' in boot_source:
            return (instance.volume_snapshot_id,
                    self.DEFAULT_VOLUME_SNAPSHOT_NAME)

    def get_image_name(self, instance_name):
        row = self._get_row_with_instance_name(instance_name)
        return row.cells[self.INSTANCES_TABLE_IMAGE_NAME_COLUMN].text

    def get_fixed_ipv4(self, name):
        row = self._get_row_with_instance_name(name)
        ips = row.cells[self.INSTANCES_TABLE_IP_COLUMN].text
        return ips.split()[0]
