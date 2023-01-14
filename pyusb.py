#!/usr/bin/env python3

import contextlib
import sys
import time
import random
import psutil

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

        # NOTE: The sleep might be able to be lower, its fine for my purposes
        #       Without the sleep, the bar will not properly recieve all
        #       information. A race condition in the dev firmware maybe?
        # sleep before calling refresh/commit/this thing [0x0d, 0x00, 0x02]
        time.sleep(0.1)
        self.dev.ctrl_transfer(0x21, 0x09, 0x0200, 0x00, [0x0d, 0x00, 0x02])


def wavelength_to_rgb(wavelength, gamma=0.8):
    '''
    This converts a given wavelength of light to an approximate RGB color value.
    The wavelength must be given in nanometers in the range from 380 nm through
    750 nm (789 THz through 400 THz).
    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html

    All code copied from dead site: https://noah.org/wiki/Wavelength_to_RGB_in_Python
    '''

    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    R *= 255
    G *= 255
    B *= 255
    return (int(R), int(G), int(B))


def percentage_to_visible_wavelength_in_rgb(percentage=0., begin_offset=0, end_offset=0):
    if percentage > 100.:
        percentage = 100.
    elif percentage < 0.:
        percentage = 0.

    freq_range_start = 380. + begin_offset
    freq_range_end   = 750. - end_offset
    freq_range       = freq_range_end - freq_range_start

    wavelength = freq_range_start + (percentage * freq_range / 100.)

    # NOTE: the function wavelenth_to_rgb will accept a range from 380-750nm
    #       values outside of that range will return (0, 0, 0)
    return wavelength_to_rgb(wavelength)


def green_to_red_percentage(percentage=0.):
    # NOTE:  510nm  ->  670nm
    #       ^green^ ->  ^red^
    # Return an RGB value between ^green^ and ^red^ based on the the percentage
    return percentage_to_visible_wavelength_in_rgb(percentage, 130, 80)


@contextlib.contextmanager
def open_usb(vendor_id, product_id):
    gu = GenericUSB(vendor_id, product_id)

    # Hardcode interface "0"
    # TODO: document multiple interfaces if needed?
    gu.detach_kernel_driver(0)

    try:
        yield gu
    finally:
        gu.close()
    

def generate_random_led():
    #r = int.from_bytes(random.randbytes(1), "big")
    #g = int.from_bytes(random.randbytes(1), "big")
    #b = int.from_bytes(random.randbytes(1), "big")

    # Pick a random number 0-100 to treat as a percentage
    random_percentage = random.randint(0,100)

    # Generage a random wavelength in the visible spectrum as RGB values
    (r, g, b) = percentage_to_visible_wavelength_in_rgb(random_percentage)

    # Enable this LED?
    enabled = bool(random.getrandbits(1))

    return generate_led(r, g, b, enabled)


def generate_led(r=0x0, g=0x0, b=0x0, enabled=True):
    led_on = 0x00
    if enabled:
        led_on = 0x01
    return [r, g, b, 0x00, 0x00, 0x00, 0x00, 0x00, led_on, 0x01, 0x00]


def main():
    with open_usb(vendor_id=0x1038, product_id=0x1134) as gu:
        #brightness = int.from_bytes(random.randbytes(1), "big")
        #print(f"Setting lightbar random brightness on scale 0-255: {brightness}")

        print("Setting lightbar max brightness")
        gu.write([0x0c, 0x00, 0xff])


        color_data = [0x0e, 0x00, 0x1e, 0x00]

        p = 0
        # Set the LED index: 0x00-0x1f are valid bytes (0-31 in base 10)
        for i in range(15):
            (r, g, b) = green_to_red_percentage(p)
            p += 3

            color_data += generate_led(r, g, b)
            color_data.append(i)

        values = psutil.cpu_percent(percpu=True)
        for i in range(15):
            (r, g, b) = green_to_red_percentage(values[i])
            color_data += generate_led(r, g, b)
            color_data.append(16 + i)

        print("Setting LEDS: byte size {}", len(color_data))
        gu.write(data=color_data, reporttype=0x0300)


if __name__ == '__main__':
    main()
