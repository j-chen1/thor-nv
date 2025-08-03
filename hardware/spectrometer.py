import os
import sys

import numpy as np

"""
import clr
from System import String
from System.Collections.Generic import List
from System.IO import *

sys.path.append(os.environ["LIGHTFIELD_ROOT"])
sys.path.append(os.environ["LIGHTFIELD_ROOT"])
clr.AddReference("PrincetonInstruments.LightFieldViewVS")
clr.AddReference("PrincetonInstruments.LightField.AutomationVS")
clr.AddReference("PrincetonInstruments.LightFieldAddInSupportServices")

import PrincetonInstruments.LightField.AddIns as AddIns
from PrincetonInstruments.LightField.AddIns import CameraSettings, DeviceType
from PrincetonInstruments.LightField.Automation import Automation
"""


class Spectrometer(object):
    def __init__(self):
        # Connect to the spectrometer via LightField

        # Follow these instructions
        pass

    def get_device(self): ...

    def set_exposure_time(
        self,
        exposure_time: int,  # Units of ms
    ): ...

    def get_total_photon_count_from_ROI(
        self,
        folder: str,
    ):
        # Save data

        seed_value = 42
        rng = np.random.default_rng(seed_value)
        return rng.integers(5000, 10000)


# def set_value(setting, value):
#     # Check for existence before setting
#     # gain, adc rate, or adc quality
#     if experiment.Exists(setting):
#         experiment.SetValue(setting, value)

# def device_found():
#     # Find connected device
#     for device in experiment.ExperimentDevices:
#         if (device.Type == DeviceType.Camera):
#             return True
#     # If connected device is not a camera inform the user
#     print("Camera not found. Please add a camera and try again.")
#     return False
