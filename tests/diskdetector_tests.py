import unittest
from lib.diskdetector import *

class DiskEventListenerTests(unittest.TestCase):

    def setUp(self):
        self.dl = DiskEventListener()
        # Clear up any drives or disks that may be detected
        self.drives = []
        self.disks = []
        self.test_device = 'test_device_1'

    def tearDown(self):
        pass

    def test_add_disk(self):
        event = DeviceEvent('add_disk', self.test_device)
        self.dl.add_disk(event)
        self.assertTrue(self.test_device in self.dl.disks)

    def test_remove_disk(self):
        event_add = DeviceEvent('add_disk', self.test_device)
        event_remove = DeviceEvent('remove_disk', self.test_device)
        self.dl.add_disk(event_add)
        self.dl.remove_disk(event_remove)
        self.assertTrue(self.test_device not in self.dl.disks)

    def test_add_device(self):
        event = DeviceEvent('add_device', self.test_device)
        self.dl.add_device(event)
        self.assertTrue(self.test_device in self.dl.devices)

    def test_remove_device(self):
        event_add = DeviceEvent('add_device', self.test_device)
        event_remove = DeviceEvent('remove_device', self.test_device)
        self.dl.add_device(event_add)
        self.dl.remove_device(event_remove)
        self.assertTrue(self.test_device not in self.dl.devices)

    def test_remove_device_with_disk(self):
        event_add = DeviceEvent('add_device', self.test_device)
        event_remove = DeviceEvent('remove_device', self.test_device)
        self.dl.add_device(event_add)
        self.dl.add_disk(event_add)
        self.dl.remove_device(event_remove)
        self.assertTrue(self.test_device not in self.dl.devices)
        self.assertTrue(self.test_device not in self.dl.disks)

    def test_device_name(self):
        event = DeviceEvent('add_device', self.test_device)
        self.dl.add_device(event)
        self.assertEqual(self.dl.device_name(0), self.test_device)

    def test_new_device_not_present(self):
        event = DeviceEvent('add_device', self.test_device)
        self.dl.add_device(event)
        self.assertFalse(self.dl.device_present(0))

    def test_add_disk_device_present(self):
        event_device = DeviceEvent('add_device', self.test_device)
        self.dl.add_device(event_device)
        event_disk = DeviceEvent('add_disk', self.test_device)
        self.dl.add_disk(event_disk)
        self.assertTrue(self.dl.device_present(0))

    def test_remove_disk_device_not_present(self):
        event_device = DeviceEvent('add_device', self.test_device)
        self.dl.add_device(event_device)
        event_add_disk = DeviceEvent('add_disk', self.test_device)
        self.dl.add_disk(event_add_disk)
        event_remove_disk = DeviceEvent('remove_disk', self.test_device)
        self.dl.remove_disk(event_remove_disk)
        self.assertFalse(self.dl.device_present(0))

