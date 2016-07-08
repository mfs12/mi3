#!/usr/bin/env python3

import pyudev

def main():
    context = pyudev.Context()
    for device in context.list_devices(subsystem="drm"):
         print('{0} ({1})'.format(device, device.device_type))

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="drm")
    for device in iter(monitor.poll, None):
        print('{0} {1}'.format(device.action, device))

if __name__ == "__main__":
        main()
