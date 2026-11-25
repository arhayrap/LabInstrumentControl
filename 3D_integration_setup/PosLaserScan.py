import numpy as np
import os
import sys
import time

if __name__ == "__main__":
    n_positions = 11
    Y_range = [106.0] # np.linspace(103.0, 105.5, 26) # [104.2]
    Z_range = [42.4] # np.linspace(42, 44, 11)
    X_range = [42.0] # np.linspace(40.7, 41.2, 21) # np.linspace(40.4, 40.9, 20)
    laser_tune = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

    file_path = "/home/daq/LecroyMount/"
    tag = "10db_attenuation_LaserTuneScan_3" # "IR_EclipseOnEdge"
    os.system(f"mkdir -p /home/daq/3D_sensors/{tag}")
    print(Z_range)
    print(X_range)
    print(Y_range)
    
    for lt in laser_tune:
        for z in Z_range:
            for x in X_range:
                for y in Y_range:
                    print(f"Position z: {z}, position x: {x}, position y: {y}")
                    file_pattern = f"--DJ_LGAD_50um_strip_{tag}_NEv1000_BV115000mV_Laser{lt}pc_Temp16C_Zpos{z}_Xpos{x}_Ypos{y}00000.trc"
                    os.system(f"python3 PosLaserScanLecroy.py --Z {z} --X {x} --Y {y} --tag {tag} --laser_tune {lt}")
                    print(f"{file_path}F8{file_pattern}")
                    print(os.path.exists(f"{file_path}F8{file_pattern}"))
                    while not (os.path.exists(f"{file_path}F8{file_pattern}")): # and os.path.exists(f"{file_path}C{file_pattern}")):
                        print("Waiting for the output files.")
                        time.sleep(3)
                    os.system(f"cp -r -f {file_path}F*{file_pattern} /home/daq/3D_sensors/{tag}/")
                    os.system(f"bash /home/daq/3D_sensors/full_processing_laser_tune.sh {z} {x} {y} {lt} {tag}")
                time.sleep(3)
    
