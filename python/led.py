from __future__ import print_function
from __future__ import division

import platform
import numpy as np
import config

# ESP8266 uses WiFi communication
if config.DEVICE == 'esp8266':
    import socket
    _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    """Find esp8266 if ip address is empty"""
    if not config.UDP_IP:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.8)
            x = True
            while x:
                sock.sendto(b'server', ("255.255.255.255", config.UDP_PORT))
                try:
                    data, addr = sock.recvfrom(1024)
                    x = False
                except socket.timeout:
                    print("Falled timeout esp8266")
            sock.close()
            if data == b'server':
                config.UDP_IP = addr[0]
            else:
                print("Falled verify esp8266")
                exit()
# Raspberry Pi controls the LED strip directly
elif config.DEVICE == 'pi':
    import neopixel
    strip = neopixel.Adafruit_NeoPixel(config.N_PIXELS, config.LED_PIN,
                                       config.LED_FREQ_HZ, config.LED_DMA,
                                       config.LED_INVERT, config.BRIGHTNESS)
    strip.begin()
elif config.DEVICE == 'blinkstick':
    from blinkstick import blinkstick
    import signal
    import sys
    #Will turn all leds off when invoked.
    def signal_handler(signal, frame):
        all_off = [0]*(config.N_PIXELS*3)
        stick.set_led_data(0, all_off)
        sys.exit(0)

    stick = blinkstick.find_first()
    # Create a listener that turns the leds off when the program terminates
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

_gamma = np.load(config.GAMMA_TABLE_PATH)
"""Gamma lookup table used for nonlinear brightness correction"""

_prev_pixels = np.tile(253, (3, config.N_PIXELS))
"""Pixel values that were most recently displayed on the LED strip"""

pixels = np.tile(1, (3, config.N_PIXELS))
"""Pixel values for the LED strip"""

_is_python_2 = int(platform.python_version_tuple()[0]) == 2

def _update_esp8266():
    """Sends UDP packets to ESP8266 to update LED strip values

    The ESP8266 will receive and decode the packets to determine what values
    to display on the LED strip. The communication protocol supports LED strips
    with a maximum of 256 LEDs.

    The packet encoding scheme is:
        |i|r|g|b|
    where
        i (0 to 255): Index of LED to change (zero-based)
        r (0 to 255): Red value of LED
        g (0 to 255): Green value of LED
        b (0 to 255): Blue value of LED
    """
    global pixels, _prev_pixels
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    # Optionally apply gamma correc tio
    p = _gamma[pixels] if config.SOFTWARE_GAMMA_CORRECTION else np.copy(pixels)
    MAX_PIXELS_PER_PACKET = 126
    # Pixel indices
    idx = range(pixels.shape[1])
    idx = [i for i in idx if not np.array_equal(p[:, i], _prev_pixels[:, i])]
    n_packets = len(idx) // MAX_PIXELS_PER_PACKET + 1
    idx = np.array_split(idx, n_packets)
    for packet_indices in idx:
        m = '' if _is_python_2 else []
        for i in packet_indices:
            if _is_python_2:
                m += chr(i) + chr(p[0][i]) + chr(p[1][i]) + chr(p[2][i])
            else:
                m.append(i)  # Index of pixel to change
                m.append(p[0][i])  # Pixel red value
                m.append(p[1][i])  # Pixel green value
                m.append(p[2][i])  # Pixel blue value
        m = m if _is_python_2 else bytes(m)
        _sock.sendto(m, (config.UDP_IP, config.UDP_PORT))
    _prev_pixels = np.copy(p)


def _update_pi():
    """Writes new LED values to the Raspberry Pi's LED strip

    Raspberry Pi uses the rpi_ws281x to control the LED strip directly.
    This function updates the LED strip with new values.
    """
    global pixels, _prev_pixels
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    # Optional gamma correction
    p = _gamma[pixels] if config.SOFTWARE_GAMMA_CORRECTION else np.copy(pixels)
    # Encode 24-bit LED values in 32 bit integers
    r = np.left_shift(p[0][:].astype(int), 8)
    g = np.left_shift(p[1][:].astype(int), 16)
    b = p[2][:].astype(int)
    rgb = np.bitwise_or(np.bitwise_or(r, g), b)
    # Update the pixels
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(p[:, i], _prev_pixels[:, i]):
            continue
        #strip._led_data[i] = rgb[i]
        strip._led_data[i] = int(rgb[i])
    _prev_pixels = np.copy(p)
    strip.show()

def _update_blinkstick():
    """Writes new LED values to the Blinkstick.
        This function updates the LED strip with new values.
    """
    global pixels
    
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    # Optional gamma correction
    p = _gamma[pixels] if config.SOFTWARE_GAMMA_CORRECTION else np.copy(pixels)
    # Read the rgb values
    r = p[0][:].astype(int)
    g = p[1][:].astype(int)
    b = p[2][:].astype(int)

    #create array in which we will store the led states
    newstrip = [None]*(config.N_PIXELS*3)

    for i in range(config.N_PIXELS):
        # blinkstick uses GRB format
        newstrip[i*3] = g[i]
        newstrip[i*3+1] = r[i]
        newstrip[i*3+2] = b[i]
    #send the data to the blinkstick
    stick.set_led_data(0, newstrip)


def update():
    """Updates the LED strip values"""
    if config.DEVICE == 'esp8266':
        _update_esp8266()
    elif config.DEVICE == 'pi':
        _update_pi()
    elif config.DEVICE == 'blinkstick':
        _update_blinkstick()
    else:
        raise ValueError('Invalid device selected')


# Execute this file to run a LED strand test
# If everything is working, you should see a sunrise.
# across the LED strip continuously
if __name__ == '__main__':
    import time
    from scipy.ndimage import gaussian_filter1d
    # Turn all pixels off
    pixels *= 0
    update()

    whiteLevel = 0
    sun = (30 * config.N_PIXELS)/100
    wakeDelay = 0.1

    def remap(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    while whiteLevel < 135:

        pixels[0,:] = whiteLevel

        currentAurora = remap(whiteLevel, 0, 135, 0, config.N_PIXELS)
        if currentAurora % 2 != 0:
            currentAurora -= 1
        
        sunStart = int((config.N_PIXELS/2)-(currentAurora/2))

        pixels[0,sunStart:sunStart+int(currentAurora)] = 127
        pixels[1,sunStart:sunStart+int(currentAurora)] = 25

        currentSun = remap(whiteLevel, 0, 135, 0, sun)
        if currentSun % 2 != 0:
            currentSun -= 1

        sunStart = int((config.N_PIXELS/2)-(currentSun/2))
        
        pixels[0,sunStart:sunStart+int(currentSun)] = 255
        pixels[1,sunStart:sunStart+int(currentSun)] = 47 + whiteLevel
        pixels[2,sunStart:sunStart+int(currentSun)] = whiteLevel

        pixels[0, :] = gaussian_filter1d(pixels[0, :], sigma=2.0)
        pixels[1, :] = gaussian_filter1d(pixels[1, :], sigma=2.0)
        pixels[2, :] = gaussian_filter1d(pixels[2, :], sigma=2.0)

        update()
        whiteLevel += 1
        time.sleep(wakeDelay)
