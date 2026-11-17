import numpy as np
import os
import sys
import time

if __name__ == "__main__":
    n_positions = 10
    Z_range = np.linspace(50.0, 50.8, n_positions)
    file_path = "/home/daq/LecroyMount/"
    for z in Z_range:
        z = np.round(z, 1)
        print(f"Position: {z}")
        file_pattern = f"8--AC_LGAD_40um_strip_NEv2000_BV115000mV_Laser20pc_Temp16C_Zpos{z}00000.trc"
        os.system(f"python3 PosScanLecroy.py --Z {z}")
        while not (os.path.exists(f"{file_path}F{file_pattern}") and os.path.exists(f"{file_path}C{file_pattern}")):
            print("Waiting for the output files.")
            time.sleep(5)
        time.sleep(10)
