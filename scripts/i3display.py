#!/usr/bin/env python3

import pyudev

def main():
    context = pyudev.Context()
    for device in context.list_devices(subsystem="drm", kernel="card0"):
        print (device)

if __name__ == "__main__":
        main()
