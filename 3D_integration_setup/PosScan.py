import numpy as np
import os
import sys
import time

if __name__ == "__main__":
    n_positions = 11
    Y_range = [104.2]
    Z_range = np.linspace(42, 44, 11)
    X_range = np.linspace(40.4, 40.9, 21) # np.linspace(40.4, 40.9, 20)
    file_path = "/home/daq/LecroyMount/"
    tag = "IR_EclipseOnEdge"
    os.system(f"mkdir -p /home/daq/3D_sensors/{tag}")
    print(Z_range)
    print(X_range)
    print(Y_range)
    
    for z in Z_range:
        for x in X_range:
            for y in Y_range:
                print(f"Position z: {z}, position x: {x}, position y: {y}")
                file_pattern = f"--AC_LGAD_40um_strip_{tag}_NEv500_BV115000mV_Laser95pc_Temp16C_Zpos{z}_Xpos{x}_Ypos{y}00000.trc"
                os.system(f"python3 PosScanLecroy.py --Z {z} --X {x} --Y {y} --tag {tag}")
                print(f"{file_path}F8{file_pattern}")
                print(os.path.exists(f"{file_path}F8{file_pattern}"))
                while not (os.path.exists(f"{file_path}F8{file_pattern}")): # and os.path.exists(f"{file_path}C{file_pattern}")):
                    print("Waiting for the output files.")
                    time.sleep(3)
                os.system(f"cp -r -f {file_path}F*{file_pattern} /home/daq/3D_sensors/{tag}/")
                os.system(f"bash /home/daq/3D_sensors/full_processing.sh {z} {x} {y} {tag}")
            time.sleep(3)
    
