#!/usr/bin/env python3

import contextlib
import sys
import time
import random

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

    def write(self, data, reporttype=0x0200):
        self.dev.ctrl_transfer(0x21, 0x09, reporttype, 0x00, data)


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
    

def generate_random_led():
    r = int.from_bytes(random.randbytes(1), "big")
    g = int.from_bytes(random.randbytes(1), "big")
    b = int.from_bytes(random.randbytes(1), "big")
    enabled = bool(random.getrandbits(1))
    return generate_led(r, g, b, enabled)


def generate_led(r=0x0, g=0x0, b=0x0, enabled=True):
    led_on = 0x00
    if enabled:
        led_on = 0x01
    return [r, g, b, 0x00, 0x00, 0x00, 0x00, 0x00, led_on, 0x01, 0x00]


def main():
    with open_usb(vendor_id=0x1038, product_id=0x1134) as gu:
        test_data = [0x0e, 0x00, 0x1e, 0x00]
        for i in range(31):
            test_data += generate_random_led()
            #test_data += generate_led(g=255)
            # Set the LED index: 0x00-0x1f are valid bytes (0-31 in base 10)
            test_data.append(i)

        print("Setting LEDS: byte size {}", len(test_data))
        gu.write(data=test_data, reporttype=0x0300)
        time.sleep(0.1)

        # Commit color settings
        #gu.write([0x0d, 0x00, 0x02] + ([0x00] * 61))
        gu.write([0x0d, 0x00, 0x02])

        # NOTE: First byte "0x0c" appears to be control byte for brightness only
        #       Second byte is unknown, but set to 0. Might be an Endianness issue
        # Brightness range 0-255 -- 0x00-0xFF
        brightness = int.from_bytes(random.randbytes(1), "big")
        print(f"Setting lightbar random brightness on scale 0-255: {brightness}")
        gu.write([0x0c, 0x00, brightness])

if __name__ == '__main__':
    main()
