#!/usr/bin/env python3

import contextlib
import sys
import time

import usb.core
import usb.util


class GenericUSB:
    def __init__(self, vendor_id, product_id):
        self.dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if self.dev is None:
            print(f"ERROR: device not found matching {vendor_id}:{product_id}")
            raise ValueError("Device not found")

    def detach_kernel_driver(self, interface):
        if self.dev.is_kernel_driver_active(interface):
            self.dev.detach_kernel_driver(interface)

    def close(self):
        usb.util.dispose_resources(self.dev)

    def write(self, data):
        self.dev.ctrl_transfer(0x21, 0x09, 0x0200, 0x00, data)


@contextlib.contextmanager
def open_usb(vendor_id=0x1038, product_id=0x1134):
    gu = GenericUSB(vendor_id, product_id)

    # Hardcode interface "0"
    # TODO: document multiple interfaces if needed?
    gu.detach_kernel_driver(0)

    try:
        yield gu
    finally:
        gu.close()
    

def generate_brightness_data(brightness=0xff):
    # NOTE: First byte "0x0c" appears to be control byte for brightness only
    #       Second byte is unknown, but set to 0. Might be an Endianness issue
    # Brightness range 0-255 -- 0x00-0xFF
    return [0x0c, 0x00, brightness]



def main():
    with open_usb(vendor_id=0x1038, product_id=0x1134) as gu:
        data = generate_brightness_data(0)
        print("Setting lightbar Min Brightness")
        gu.write(data)
        print(f"Successfully wrote data to usb: {data}")

        time.sleep(2)

        data = generate_brightness_data(255)
        print("Setting lightbar Max Brightness")
        gu.write(data)
        print(f"Successfully wrote data to usb: {data}")


if __name__ == '__main__':
    main()
