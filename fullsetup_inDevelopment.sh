#!/usr/bin/env bash

# Note that the Keysight IO Libraries should be downloaded manually.
# You will also need to manually change (and/or check) the Keysight
# library path in iFunctions_class_v03.py. I refer to this variable:
# ----> DEFAULT_KEYSIGHT_VISA_LIBRARY_PATH.


ENV_NAME="$1"

# Making directories where the DAQ data will be stored
mkdir ../0_RawData_h5           # This is where the raw data from scope will be copied
mkdir ../1_ConvertedRoots       # ...where the converted h5 files (combined waveforms in root format) will be
mkdir ../2_PreprocessedRoots    # ...where TimingDAQ-preprocessed roots will be


# Creating conda environment with required packages
packages=(
    python=3.12
    numpy
    matplotlib
    scipy
    pandas
    h5py

    pyvisa
    pyvisa-py
    gpib-ctypes
    zeroconf

    pyyaml

    gxx

    root
    uproot
)

conda create --name "$ENV_NAME" -c conda-forge --override-channels \
    "${packages[@]}" -y


# TimingDAQ setup
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
cp TimingDAQ_mod.zip ../
unzip ../TimingDAQ_mod.zip -d ../
rm ../TimingDAQ_mod.zip
cd ../TimingDAQ_mod
make -j8

cd ../LabInstrumentControl
