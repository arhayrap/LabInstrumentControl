import h5py
import os

file = "TESTING-v01-Ch4-NEv5000-Neg100V.h5"

filepath = os.path.join(file)

with h5py.File(filepath, "r+") as h5:
    waveforms = h5["Waveforms"]

    print("Before:", list(waveforms.keys()))

    waveforms.move("Channel 3", "Channel 4")

    print("After:", list(waveforms.keys()))
