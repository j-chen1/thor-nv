"""
Python Interface for the Tisaph laser by M-Squared

Authors: Jenny Chen <jennychen42@berkeley.edu>,

UC Berkeley, 2025
"""

## Imports
import pylablib as pll
from pylablib.devices import M2


class TiSaph(object):
    def __init__(self, IP_address, port_number):
        # self.laser = M2.Solstis(IP_address, port_number, use_websocket=True)
        self.laser = None

    def get_wavelength(self):
        # return self.laser.get_coarse_wavelength()
        return 800

    def set_wavelength(self, wavelength: float):
        # self.laser.coarse_tune_wavelength(wavelength=wavelength)
        return True
