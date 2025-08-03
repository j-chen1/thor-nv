# Imports
import csv
import os
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import hardware.solstis as Solstis
import hardware.spectrometer as Spect

current_path = str(Path(__file__).parents[0])


def sweep_wavelength(
    start_wavelength_nm: float,
    end_wavelength_nm: float,
    step_nm: float,
    exposure_time_sec: float,
    wait_time_sec: float,
    power_532_W: float = None,
    power_probe_W: float = None,
    save_data: bool = True,
):
    data_folder = None

    if save_data:
        # Make timestamp for sweep
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        # Write sweep parameters
        data_folder = write_initial_param(
            timestamp,
            start_wavelength_nm,
            end_wavelength_nm,
            step_nm,
            power_532_W,
            power_probe_W,
            exposure_time_sec,
            wait_time_sec,
        )

    # Initialize Tisaph
    IP_address = ...
    port_number = ...
    laser = Solstis.TiSaph(IP_address=IP_address, port_number=port_number)

    # Initialize spectrometer
    spectrometer = Spect.Spectrometer()

    # Make sure 532 nm laser is on and at sufficient power
    # Warm up TiSaph and make sure the optics have thermalized

    # Perform sweep of wavelength
    wavelengths = np.arange(start_wavelength_nm, end_wavelength_nm, step_nm)
    total_counts = np.zeros_like(wavelengths)

    for i in range(len(wavelengths)):
        # Set wavelength in Tisaph
        laser.set_wavelength(wavelengths[i])

        # Wait 0.5 sec for the wavelength to lock
        time.sleep(wait_time_sec)

        # Take image with spectrometer and saves data if data_folder is not None
        total_count = spectrometer.get_total_photon_count_from_ROI(folder=data_folder)

        total_counts[i] = total_count
        if save_data:
            wavelength_counts_data = np.zeros((2, len(wavelengths)))
            wavelength_counts_data[0], wavelength_counts_data[1] = (
                wavelengths,
                total_counts,
            )
            np.savetxt(
                f"{data_folder}/data_summary.txt",
                wavelength_counts_data.T,
                delimiter=",",
            )

    return timestamp


def write_initial_param(
    timestamp: str,
    start_wavelength_nm: float,
    end_wavelength_nm: float,
    step_nm: float,
    power_532_W: float,
    power_probe_W: float,
    exposure_time_sec: float,
    wait_time_sec: float,
):
    # Make folder labeled as YMD for current day if doesn't exist
    newYMD_folder = f"{current_path}/data/{timestamp.split('-')[0]}"
    if not os.path.exists(newYMD_folder):
        os.makedirs(newYMD_folder)

    # Add folder labeled by timestamp formatted as YMD-HMS
    newYMD_HMS_folder = f"{newYMD_folder}/{timestamp}"
    os.makedirs(newYMD_HMS_folder)

    # The new row to append
    new_row = [
        timestamp,
        start_wavelength_nm,
        end_wavelength_nm,
        step_nm,
        power_532_W,
        power_probe_W,
        exposure_time_sec,
        wait_time_sec,
    ]

    # Append to logger.csv file with experimental parameters
    with open(f"{current_path}/data/logger.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(new_row)

    return newYMD_HMS_folder


def get_logger_param(timestamp: str):
    # Get experimental parameters at timestamp from logger.csv
    logger_param = {}

    with open(f"{current_path}/data/logger.csv", mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("Timestamp") == timestamp:
                logger_param = row

    return logger_param


def get_data_summary(timestamp: str):
    # Get data summary with photon counts vs. wavelength from timestamped folder
    data_summary_path = (
        f"{current_path}/data/{timestamp.split('-')[0]}/{timestamp}/data_summary.txt"
    )
    wavelength_counts = np.loadtxt(data_summary_path, delimiter=",")

    return wavelength_counts


def plot_wavelength_sweep(timestamp: str):
    # Read parameters from logger file
    exp_param = get_logger_param(timestamp)

    # Get the photon counts vs. wavelengths probed at with the TiSaph laser
    wavelength_counts = get_data_summary(timestamp)
    wavelengths, photon_counts = wavelength_counts[0], wavelength_counts[1]

    # Plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(wavelengths, photon_counts)
    ax.set_xlabel("Probe wavelength (nm)")
    ax.set_ylabel("Total photon counts")

    # Make text box displaying experimental parameters
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    # timestamp = exp_param["Timestamp"]
    print(exp_param)
    start_wavelength_nm = exp_param["start_wavelength_nm"]
    end_wavelength_nm = exp_param["end_wavelength_nm"]
    step_nm = exp_param["step_nm"]
    power_532_W = exp_param["power_532_W"]
    power_probe_W = exp_param["power_probe_W"]
    exposure_time_sec = exp_param["exposure_time_sec"]
    wait_time_sec = exp_param["wait_time_sec"]
    text_str = f"""Range: ({start_wavelength_nm: .2f}, {end_wavelength_nm: .2f}, {step_nm})\n
                    532nm power = {power_532_W: .3f}W\n
                    TiSaph power = {power_probe_W}W\n
                    Exposure time = {exposure_time_sec / 1e-3: .0f} ms\n
                    Wait time = {wait_time_sec: .2f} s
                    """
    ax.text(
        0.05,
        0.95,
        text_str,
        transform=ax.transAxes,
        fontsize=14,
        verticalalignment="top",
        bbox=props,
    )

    plt.show()


if __name__ == "__main__":
    # timestamp = sweep_wavelength(
    #     start_wavelength_nm=790,
    #     end_wavelength_nm=830,
    #     step_nm=1,
    #     save_data=True,
    #     exposure_time_sec=100e-3,
    #     wait_time_sec=0.05,
    #     power_532_W=10e-3,
    #     power_probe_W=100e-3,
    # )
    plot_wavelength_sweep("20250803-104120")

    pass
