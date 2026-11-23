import numpy as np
import os
import sys
import time

if __name__ == "__main__":
    n_positions = 11
    Y_range = np.linspace(103.2, 105.4, 101)
    Z_range = [41.5]
    X_range = [41.72]
    file_path = "/home/daq/LecroyMount/"
    print(Z_range)
    print(X_range)
    print(Y_range)
    
    for z in Z_range:
        for x in X_range:
            for y in Y_range:
                print(f"Position z: {z}, position x: {x}, position y: {y}")
                file_pattern = f"8--AC_LGAD_40um_strip_NEv500_BV115000mV_Laser20pc_Temp16C_Zpos{z}_Xpos{x}_Ypos{y}00000.trc"
                os.system(f"python3 PosScanLecroy.py --Z {z} --X {x} --Y {y}")
                while not (os.path.exists(f"{file_path}F{file_pattern}")): # and os.path.exists(f"{file_path}C{file_pattern}")):
                    print("Waiting for the output files.")
                    time.sleep(5)
                # os.system("cd ../../3D_sensors/")
                os.system(f"bash /home/daq/3D_sensors/full_processing.sh {z} {x} {y}")
                # os.system("cd -")
            time.sleep(10)
    
