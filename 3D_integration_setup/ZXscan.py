import numpy as np
import os
import sys
import time

if __name__ == "__main__":
    n_positions = 11
    # Z_range = np.linspace(50.0, 50.8, n_positions)
    Z_range = [41.5] #  np.linspace(40.24, 50.8, 6)
    X_range = np.linspace(41.4, 41.8, 41)
    file_path = "/home/daq/LecroyMount/"
    print(Z_range)
    print(X_range)
    
    for z in Z_range:
        for x in X_range:
            print(f"Position z: {z}, position x: {x}")
            file_pattern = f"8--AC_LGAD_40um_strip_NEv500_BV115000mV_Laser20pc_Temp16C_Zpos{z}_Xpos{x}00000.trc"
            os.system(f"python3 PosScanLecroy.py --Z {z} --X {x}")
            while not (os.path.exists(f"{file_path}F{file_pattern}")): # and os.path.exists(f"{file_path}C{file_pattern}")):
                print("Waiting for the output files.")
                time.sleep(5)
        time.sleep(10)
    
