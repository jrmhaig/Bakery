import dbus
from gi.repository import GLib

class DeviceAddedListener:
    #def __init__(self, devices):
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.hal_manager_obj = self.bus.get_object(
                                   "org.freedesktop.Hal",
                                   "/org/freedesktop/Hal/Manager")

        self.hal_manager = dbus.Interface(self.hal_manager_obj,
                                          "org.freedesktop.Hal.Manager")

        self.hal_manager.connect_to_signal("DeviceAdded", self._add_filter)
        self.hal_manager.connect_to_signal("DeviceRemoved", self._rem_filter)

        self.volumes = []
        self.devices = []

    def _add_filter(self, uid):
        device_obj = self.bus.get_object("org.freedesktop.Hal", uid)
        device = dbus.Interface(device_obj, "org.freedesktop.Hal.Device")

        if device.QueryCapability("volume"):
            self.volumes.append(uid)
            return self.do_something(device)

    def _rem_filter(self, uid):
        vols = []
        for uid in self.volumes:
            try:
                device_obj = self.bus.get_object("org.freedesktop.Hal", uid)
                device = dbus.Interface(device_obj, "org.freedesktop.Hal.Device")
                if device.QueryCapability("volume"):
                    vols.append(uid)
                    print("Still got it!")
                else:
                    print("Lost one!")
            except:
                print("Lost one!")
        self.volumes = vols

    def do_something(self, volume):
        device_file = volume.GetProperty("block.device")
        #devices.append(device_file)
        label = volume.GetProperty("volume.label")
        fstype = volume.GetProperty("volume.fstype")
        mounted = volume.GetProperty("volume.is_mounted")
        mount_point = volume.GetProperty("volume.mount_point")
        try:
            size = volume.GetProperty("volume.size")
        except:
            size = 0

        print("New storage device detectec:")
        print("  device_file: %s" % device_file)
        print("  label: %s" % label)
        print("  fstype: %s" % fstype)
        if mounted:
            print("  mount_point: %s" % mount_point)
        else:
            print("  not mounted")
        print("  size: %s (%.2fGB)" % (size, float(size) / 1024**3))

if __name__ == '__main__':
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    DeviceAddedListener()
    loop.run()
