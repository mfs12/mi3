#!/usr/bin/env python2

import dbus
import gobject
import os
import pynotify
import sys

from dbus.mainloop.glib import DBusGMainLoop

class Pm_message:
    def __init__(self, urgency, message):
        self.urgency = urgency
        self.message = message

    def send(self):
        if not pynotify.is_initted():
            print (" msg: " + self.message)
            return
        n = pynotify.Notification(self.message)
        n.set_urgency(self.urgency)
        n.set_timeout(6000)
        n.show()

class Pmd:
    def __init__(self, low_limit, crit_limit):
        self.low_limit = low_limit
        self.crit_limit = crit_limit

        self.msg_low = Pm_message(pynotify.URGENCY_NORMAL, "battery level is low")
        self.msg_crit = Pm_message(pynotify.URGENCY_CRITICAL, "battery level is critical low")

        self.bus = dbus.SystemBus()
        self.session = self.bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
        self.session_iface = dbus.Interface(self.session, "org.freedesktop.login1.Manager")
        self.upower = self.bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower")
        self.upower_iface = dbus.Interface(self.upower, "org.freedesktop.DBus.Properties")
        self.upower.connect_to_signal("PropertiesChanged", pmd_handler_upower_update)
        self.bat = self.bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower/devices/battery_BAT1")
        self.bat_iface = dbus.Interface(self.bat, "org.freedesktop.DBus.Properties")
        self.bat.connect_to_signal("PropertiesChanged", pmd_handler_update)

    def is_on_battery(self):
        return self.upower_iface.Get('org.freedesktop.UPower', 'OnBattery') == True

    def is_lid_closed(self):
        return self.upower_iface.Get('org.freedesktop.UPower', 'LidIsClosed') == True

    def get_percentage(self):
        return int(self.bat_iface.Get('org.freedesktop.UPower.Device', 'Percentage'))

    def is_low(self):
        return self.get_percentage() < self.low_limit

    def is_crit(self):
        return self.get_percentage() < self.crit_limit

    def can_suspend(self):
        return self.session_iface.CanSuspend() == 'yes'

    def can_hybrid_sleep(self):
        #return self.session_iface.CanHybridSleep() == 'yes'
        return False

    def can_hibernate(self):
        return self.session_iface.CanHibernate() == 'yes'

    def lock(self):
#        # TODO or do i3pm stuff if i3pm is running
#        return self.session_iface.LockSessions('org.freedesktop.login1.Manager')
        os.system("i3pm lock")

    def suspend(self):
        return self.session_iface.Suspend(True)

    def hibernate(self):
        return self.session_iface.Hibernate(True)

    def hybrid_sleep(self):
        return self.session_iface.HybridSleep(True)

def pmd_handler_upower_update(interface_name, changed_properties, invalidated_properties):
    global pmd

    if pmd.is_lid_closed():
        pmd.lock()
        return

def pmd_handler_update(interface_name, changed_properties, invalidated_properties):
    global pmd

#    print ("pmd_handler_update: iname: " + interface_name)
#    print (" changed: ")
#    for entry in changed_properties:
#        print (entry)
#    print ("invalidated: ")
#    for entry in invalidated_properties:
#        print (entry)

    if not pmd.is_on_battery():
        return

    if pmd.is_low():
        pmd.msg_low.send()

    if pmd.is_crit():
        pmd.msg_crit.send()
        pmd.lock()

        if pmd.can_hybrid_sleep():
            pmd.hybrid_sleep()
        elif pmd.can_hibernate():
            pmd.hibernate()
        elif pmd.can_suspend():
            pmd.suspend()
        else:
            print ("neither hybrid sleep, hibernate or suspend work")

    return

def main():
    loop = gobject.MainLoop()
    loop.run()

if __name__ == "__main__":
    print ("starting " + sys.argv[0] + "...")

    DBusGMainLoop(set_as_default=True)
    if not pynotify.init(sys.argv[0]):
        print ("failed to init pynotify")
        exit(1)

    low = 12
    crit = 10
    if len(sys.argv) >= 2:
        low = int(sys.argv[1])

    if len(sys.argv) >= 3:
        crit = int(sys.argv[2])

    print "low", low, "crit", crit
    pmd = Pmd(low, crit)

    #print "low", pmd.is_low()
    #print "ciritcal", pmd.is_crit()
    #pmd.msg_low.send()

    main()
