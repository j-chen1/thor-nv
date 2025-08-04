# Import modules
import ctypes
import glob
import os
import string
import sys
import time
from typing import Callable, Optional

import clr
import numpy as np
import serial

# Import c compatible List and String
from System import String
from System.Collections.Generic import List

# Import System.IO for saving and opening files
from System.IO import *
from System.Runtime.InteropServices import GCHandle, GCHandleType, Marshal
from System.Threading import AutoResetEvent

# Add needed dll references
sys.path.append(os.environ["LIGHTFIELD_ROOT"])
sys.path.append(os.environ["LIGHTFIELD_ROOT"] + "\\AddInViews")
clr.AddReference("PrincetonInstruments.LightFieldViewV5")
clr.AddReference("PrincetonInstruments.LightField.AutomationV5")
clr.AddReference("PrincetonInstruments.LightFieldAddInSupportServices")

# PI imports
from PrincetonInstruments.LightField.AddIns import (
    CameraSettings,
    DeviceType,
    ExperimentSettings,
    IDevice,
    ImageDataFormat,
    SpectrometerSettings,
)
from PrincetonInstruments.LightField.Automation import Automation

# class Spectrometer(object):
#     def __init__(self):
#         # Connect to the spectrometer via LightField

#         # Follow these instructions
#         pass

#     def get_device(self): ...

#     def set_exposure_time(
#         self,
#         exposure_time: int,  # Units of ms
#     ): ...

#     def get_total_photon_count_from_ROI(
#         self,
#         folder: str,
#     ):
#         # Save data

#         return np.random.randint(5000, 10000)


# def clearSer(obj):
#     obj.reset_input_buffer()
#     obj.reset_output_buffer()


# def convert_buffer(net_array, image_format):
#     src_hndl = GCHandle.Alloc(net_array, GCHandleType.Pinned)
#     try:
#         src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()

#         # Possible data types returned from acquisition
#         if image_format == ImageDataFormat.MonochromeUnsigned16:
#             buf_type = ctypes.c_ushort * len(net_array)
#         elif image_format == ImageDataFormat.MonochromeUnsigned32:
#             buf_type = ctypes.c_uint * len(net_array)
#         elif image_format == ImageDataFormat.MonochromeFloating32:
#             buf_type = ctypes.c_float * len(net_array)

#         cbuf = buf_type.from_address(src_ptr)
#         resultArray = np.frombuffer(cbuf, dtype=cbuf._type_)

#     # Free the handle
#     finally:
#         if src_hndl.isAllocated:
#             src_hndl.Free()
#     # Make a copy of the buffer
#     return np.cpy(resultArray)


# def ManipulateImageData(dat, buff):
#     im = convert_buffer(dat, buff.Format)
#     im = np.reshape(im, (height, width))
#     return im


### Important


class LightFieldAutomation:
    def __init__(self, experiment_name: str, data_loc: str):
        # Create the LightField Application, opens up a secondary LightField
        # Make sure no other windows of LightField are open
        auto = Automation(True, List[String]())
        self.experiment = auto.LightFieldApplication.Experiment  # Get experiment object
        self.acquireCompleted = AutoResetEvent(False)
        self.datarun_loc = data_loc

        # Load a particular experiment file
        self.experiment.Load(experiment_name)
        self.experiment.ExperimentCompleted += self.experiment_completed

        # Make sure spectrometer files save to given folder location
        self.set_acquired_data_loc(data_loc=self.datarun_loc)

        # Get ROI dimensions (it's best to customize the ROI yourself with the live LightField application)
        # For more details, go to the guides section of the Wiki
        self.width = self.experiment.GetValue(
            CameraSettings.SensorInformationActiveAreaWidth
        )
        self.height = self.experiment.GetValue(
            CameraSettings.SensorInformationActiveAreaHeight
        )

        self.data_analysis_func = LightFieldAutomation.do_nothing

    def get_experiment(self):
        return self.experiment

    def experiment_completed(self, sender, event_args):
        print("...Acquisition Complete!")
        self.acquireCompleted.Set()
        self.experiment.ImageDataSetReceived -= self.experiment_data_ready

    def experiment_data_ready(self, sender, event_args):
        if self.experiment.IsReadyToRun:
            global i
            frames = event_args.ImageDataSet.Frames
            i += frames
            buffer = event_args.ImageDataSet.GetFrame(0, frames - 1)
            image_data = buffer.GetData()
            data_array = self.manipulate_image_data(image_data, buffer)
            self.data_analysis_func(data_array)

        return data_array

    def acquire_and_lock(self, exp_name: str, probe_wavelength_nm: float):
        self.experiment.ImageDataSetReceived += self.experiment_data_ready
        print("Acquiring...")

        # Give custom name for each saved data file (e.g. what wavelength the TiSaph laser is at)
        exp_name += f"-{probe_wavelength_nm: .2f}"
        self.InitializeFilenameParams()
        self.experiment.setValue(
            ExperimentSettings.FileNameGenerationBaseFileName, exp_name
        )

        # Acquire data
        self.experiment.Acquire()
        self.acquireCompleted.WaitOne()

    def acquire_analyze_and_save(
        self,
        exp_name: str,
        probe_wavelength_nm: float,
        average_exposures: bool = True,
        num_exposures: int = 1,
        exposure_time_ms: float = None,
        img_func: Callable[
            [np.ndarray], None | Optional[float] | Optional[np.ndarray]
        ] = None,
    ):
        if average_exposures:
            # Set averaging to true
            ...
        else:
            ...

        # Set the number of exposures
        self.set_exposures_per_frame(num_exposures)
        # Set exposure time
        self.set_exposure_time(exposure_time_ms)

        # Choose how the ndarray image is processed when it is acquired
        if img_func is None:
            self.data_analysis_func = LightFieldAutomation.do_nothing
        else:
            self.data_analysis_func = img_func

        ## TODO: Decide what the frame analysis does (only process or save the data as well?)

        # Acquire and save data
        self.acquire_and_lock(exp_name, probe_wavelength_nm)

        return

    ##### Custom image analysis methods

    def calculate_total_counts(self, im: np.ndarray):
        return np.sum(im)

    @staticmethod
    def do_nothing(im: np.ndarray):
        return

    ##### Image processing methods

    def convert_buffer(self, net_array, image_format):
        src_hndl = GCHandle.Alloc(net_array, GCHandleType.Pinned)
        try:
            src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()

            # Possible data types returned from acquisition
            if image_format == ImageDataFormat.MonochromeUnsigned16:
                buf_type = ctypes.c_ushort * len(net_array)
            elif image_format == ImageDataFormat.MonochromeUnsigned32:
                buf_type = ctypes.c_uint * len(net_array)
            elif image_format == ImageDataFormat.MonochromeFloating32:
                buf_type = ctypes.c_float * len(net_array)

            cbuf = buf_type.from_address(src_ptr)
            resultArray = np.frombuffer(cbuf, dtype=cbuf._type_)

        # Free the handle
        finally:
            if src_hndl.isAllocated:
                src_hndl.Free()
        # Make a copy of the buffer
        return np.cpy(resultArray)

    def manipulate_image_data(self, dat, buff):
        im = self.convert_buffer(dat, buff.Format)
        im = np.reshape(im, (self.height, self.width))
        return im

    ##### Miscellaneous methods

    def InitializeFilenameParams(self):
        # experiment.SetValue(ExperimentSettings.FileNameGenerationAttachIncrement, True)
        # experiment.SetValue(ExperimentSettings.FileNameGenerationIncrementNumber, 1)
        # experiment.SetValue(ExperimentSettings.FileNameGenerationIncrementMinimumDigits, 2)
        self.experiment.SetValue(ExperimentSettings.FileNameGenerationAttachDate, False)
        self.experiment.SetValue(ExperimentSettings.FileNameGenerationAttachTime, True)

    ##### Getter and setter methods

    def set_acquired_data_loc(self, data_loc: str):
        self.experiment.setValue(
            ExperimentSettings.FileNameGenerationDirectory, data_loc
        )

    def select_grating(
        self,
        blaze_wavelength: int,
        groove_density: int,
        grating_index: int,
        turret_index: int,
    ):
        self.experiment.SetValue(
            SpectrometerSettings.GratingSelected,
            f"[{blaze_wavelength}nm,{groove_density}][{grating_index}][{turret_index}]",
        )

    def set_exposure_time(self, exposure_ms: int):
        self.experiment.SetValue(CameraSettings.ShutterTimingExposureTime, exposure_ms)

    def set_num_frames_to_store(self, num_frames: int):
        self.experiment.SetValue(
            ExperimentSettings.AcquisitionFramesToStore, num_frames
        )

    def set_exposures_per_frame(self, num_exposures: int, avg_over: bool = True):
        self.experiment.SetValue(
            ExperimentSettings.OnlineProcessingFrameCombinationFramesCombined,
            num_exposures,
        )

        # Set averaging or summing over exposures to True
        if avg_over:
            ...
