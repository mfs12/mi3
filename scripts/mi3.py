#!/usr/bin/python2 -i

import dbus
#import dbus.mainloop.glib
import gobject
import logging
import os
import pynotify
import sys
import pyudev

def pynotify_init():
    if not pynotify.is_initted():
        pynotify.init("mi3")


class Mi3Notify:
    def __init__(self, message="", urgency=pynotify.URGENCY_NORMAL, timeout=6000):
        self.message = message
        self.urgency = urgency
        self.timeout = timeout

        self.note = pynotify.Notification(self.message)
        self.note.set_urgency(self.urgency)
        self.note.set_timeout(self.timeout)

    def send(self):
        if pynotify.is_initted():
            self.note.show()
        else:
            print(
                    " u: " + str(self.urgency) + ", "
                    " t: " + str(self.timeout) + ", "
                    " m: " + str(self.message)
                    )

class Mi3Thread:
    def __init__(self, handler):
        self.handler = handler
    
    def name_get(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def run(self):
        pass

    def is_running(self):
        pass


class Mi3Session:
    def __init__(self):

        self.bus = dbus.bus.BusConnection(dbus.bus.BUS_SYSTEM)
        self.login = self.bus.get_object(
                "org.freedesktop.login1",
                "/org/freedesktop/login1/seat/self"
                )
        self.seat0 = self.bus.get_object(
                "org.freedesktop.DisplayManager",
                "/org/freedesktop/DisplayManager/Seat0"
                )

    def lock(self):
        self.seat0.Lock(dbus_interface="org.freedesktop.DisplayManager.Seat")

    def greet(self):
        self.seat0.SwitchToGreeter(dbus_interface="org.freedesktop.DisplayManager.Seat")

    def logout(self):
        self.login.Terminate(dbus_interface="org.freedesktop.login1.Seat")

class Mi3Power:
    def __init__(self, low_limit=10, crit_limit=5, handler=None):

        self.bus = dbus.bus.BusConnection(dbus.bus.BUS_SYSTEM)
        self.login = self.bus.get_object(
                "org.freedesktop.login1",
                "/org/freedesktop/login1"
                )
        self.power = self.bus.get_object(
                "org.freedesktop.UPower",
                "/org/freedesktop/UPower"
                )
        self.battery = self.bus.get_object(
                "org.freedesktop.UPower",
                "/org/freedesktop/UPower/devices/battery_BAT1"
                )

        if handler:
            register_battery_handler(handler)

    def hibernate(self):
        self.login.Hibernate(True, dbus_interface="org.freedesktop.login1.Manager")

    def suspend(self):
        self.login.Suspend(True, dbus_interface="org.freedesktop.login1.Manager")

    def poweroff(self):
        self.login.PowerOff(True, dbus_interface="org.freedesktop.login1.Manager")

    def restart(self):
        self.login.Restart(True, dbus_interface="org.freedesktop.login1.Manager")

    def is_on_battery(self):
        return self.power.Get(
                "org.freedesktop.UPower", "OnBattery",
                dbus_interface="org.freedesktop.DBus.Properties"
                ) == True

    def get_battery_percentage(self):
        return self.battery.Get(
                "org.freedesktop.UPower.Device", "Percentage",
                dbus_interface="org.freedesktop.DBus.Properties"
                )

    def get_battery_powersupply(self):
        return self.battery.Get(
                "org.freedesktop.UPower.Device", "PowerSupply",
                dbus_interface="org.freedesktop.DBus.Properties"
                ) == True

    def is_lid_closed(self):
        return self.power.Get(
                "org.freedesktop.UPower", "LidIsClosed",
                dbus_interface="org.freedesktop.DBus.Properties"
                ) == True

    def register_battery_handler(self, handler):
        self.battery.connect_to_signal(
                "PropertiesChanged",
                handler,
                dbus_interface="org.freedesktop.DBus.Properties"
                )
        self.power.connect_to_signal(
                "PropertiesChanged",
                handler,
                dbus_interface="org.freedesktop.DBus.Properties"
                )


class Mi3Audio:
    def __init__(self):
        #self.audio = self.bus.get_object("org.pulseaudio.Server") TODO lookup
        self.bus = dbus.bus.Connection("unix:path=/run/user/1000/pulse/dbus-socket")
        self.core = self.bus.get_object("org.PulseAudio.Core1", "/org/pulseaudio/core1")
        self.sinks = [
                self.bus.get_object("org.PulseAudio.Core1", "/org/pulseaudio/core1/sink0"), 
                self.bus.get_object("org.PulseAudio.Core1", "/org/pulseaudio/core1/sink1")
                ]
        self.streams = []

    def mute_all(self):
        for sink in self.sinks:
            sink.Set(
                    "org.PulseAudio.Core1.Device", "Mute", True,
                    dbus_interface="org.freedesktop.DBus.Properties"
                    )

    def unmute_all(self):
        for sink in self.sinks:
                sink.Set(
                        "org.PulseAudio.Core1.Device", "Mute", False,
                        dbus_interface="org.freedesktop.DBus.Properties"
                        )

    def get_volume(self):
        for sink in self.sinks:
                vol = sink.Get(
                        "org.PulseAudio.Core1.Device", "Volume",
                        dbus_interface="org.freedesktop.DBus.Properties"
                        )
                print('{0} {1}'.format(sink, vol))

    def volume_up(self):
        pass

    def volume_down(self):
        pass

    def launch_pavucontrol(self):
        pass

    def dbus_handler_system_changed(self):
        pass

class Mi3Event:
    def __init__(self):
        self.name = "event"

    def handler(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class Mi3EventSocket(Mi3Event):
    def __init__(self):
        self.name = "event socket"
        self.socket = "i3 --get-socketpath"

    def handler(self):
        if not self.socket:
            pass

class Mi3EventBattery(Mi3Event):
    def __init__(self, low_limit=12, crit_limit=5):

        self.name = "event battery"
        self.low_limit = low_limit
        self.crit_limit = crit_limit
        self.power = Mi3Power(handler=self.handler)
        self.session = Mi3Session()
    
    def handler(self):
        soc = self.power.get_battery_percentage()
        if (soc <= self.crit_limit):
            Mi3Notify("battery critical").send()
            self.session.lock()
            self.power.suspend()

        if (soc <= self.low_limit):
            Mi3Notify("battery low").send()

        return

class Mi3EventLidClose(Mi3Event):
    def __init__(self):
        self.name = "event lid close"
        self.power = Mi3Power()
        self.session = Mi3Session()

    def handler(self):
        if self.power.is_lid_closed():
            self.session.lock()
            self.power.suspend()


class Mi3EventDrm(Mi3Event):
    def __init__(self):
        self.name = "event drm"

        self.udev = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(context)
        self.monitor.filter_by(subsystem="drm")
        self.observer = pyudev.MonitorObserver(self.monitor, handler)

        for device in self.udev.list_devices(subsystem="drm"):
            print('{0} ({1})'.format(device, device.device_type))

    def handler(self):
        os.system("xrandr --auto")

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()

   
class Mi3d:
    def __init__(self):
        self.events = [
                Mi3EventSocket(),
                Mi3EventBattery(),
                Mi3EventLidClose(),
                Mi3EventDrm() 
                ]

        #self.main_loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.main_loop = gobject.MainLoop()
        dbus.set_default_loop(self.main_loop)

    def start_threads(self):
        for thread in self.threads:
            thread.start()
        pass

    def run(self):
        self.main_loop.run()

    def end_treads(self):
        for thread in self.threads:
            thread.stop()

    def start(self):
        start_threads()

        run()

        end_threads()

class Mi3Cl():
    def __init__(self, command=None):
        self.command = command

    def suspend(self):
        self.lock()
        Mi3Power().suspend()

    def poweroff(self):
        Mi3Power().poweroff()

    def restart(self):
        Mi3Power().restart()

    def lock(self):
        Mi3Session().lock()

    def logout(self):
        Mi3Session().logout()




def main(cli=False):
    pass

if __name__ == "__main__":
    print ("starting " + sys.argv[0] + "...")

    if not pynotify.init(sys.argv[0]):
        print ("failed to init pynotify")
        exit(1)

    if len(sys.argv) >= 2:
        low = int(sys.argv[1])

    if len(sys.argv) >= 3:
        crit = int(sys.argv[2])

    pm_loop()
    display_loop()
