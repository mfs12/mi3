#!/usr/bin/env python2

import pyudev
import os

def main():
    context = pyudev.Context()
    for device in context.list_devices(subsystem="drm"):
         print('{0} ({1})'.format(device, device.device_type))

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="drm")
    for device in iter(monitor.poll, None):
        print('{0} {1}'.format(device.action, device))
        os.system("xrandr --auto")

if __name__ == "__main__":
        main()
