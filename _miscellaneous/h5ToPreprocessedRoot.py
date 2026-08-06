import subprocess
import numpy as np
from concurrent.futures import ThreadPoolExecutor

def run_command(command):
    return subprocess.run(command, shell=True, check=True).returncode


biasVoltages = [-110]



commands = []
for bv in biasVoltages:
    commands.append(
        'python reconstructionTools/convertH5ToROOT.py '
        f'../0_RawData_h5/RT_3x3_vb113v_mcp4300_ch1.h5 '
        f'../0_RawData_h5/RT_3x3_vb113v_mcp4300_ch2.h5 '
        f'-o ../1_ConvertedRoots/conv_RT_3x3_vb113v_mcp4300.root'
        )

with ThreadPoolExecutor(max_workers=6) as executor:
    returnCodes = list(executor.map(run_command, commands))
    executor.shutdown(wait=True)


print("===")
print("===")
print("===")
print("===")
print("===")

print("Starting preprocessing...")

print("===")
print("===")
print("===")
print("===")
print("===")


commands = []
for bv in biasVoltages:
    commands.append(
        '../TimingDAQ_mod/NetScopeStandaloneDat2Root '
        f'--input_file="../1_ConvertedRoots/conv_RT_3x3_vb113v_mcp4300.root" '
        '--config="configs/Keysight_v01.config" '
        '--save_meas=true --num_channels=2 --num_samples=5120 --verbose=true '
        f'--output_file="../2_PreprocessedRoots/prep_RT_3x3_vb113v_mcp4300.root"'
    )

with ThreadPoolExecutor(max_workers=6) as executor:
    returnCodes = list(executor.map(run_command, commands))


print(returnCodes)
