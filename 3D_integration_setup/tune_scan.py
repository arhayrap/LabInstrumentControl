import os
import sys
import numpy as np
import glob
import argparse
import json
from laser_homing import load_pixel_positions
from motion_safety import TRAVEL_MAX_MM, safe_position_mm

argparser = argparse.ArgumentParser(description="Tune Scan Script")
argparser.add_argument("--start", type=int, default=96, help="Starting TUNE value (default: 96)")
argparser.add_argument("--midpoint", type=int, default=80, help="Midpoint TUNE value (default: 80)")
argparser.add_argument("--end", type=int, default=0, help="Ending TUNE value (default: 0)")
argparser.add_argument("--date", type=str, default='Sep10_4', help="Date for output directory (default: Sep10_4)")
argparser.add_argument("--row", type=int, default=0, help="Row number (default: 0)")
argparser.add_argument("--col", type=int, default=15, help="Column number (default: 15)")
argparser.add_argument("--moduleid", type=int, default=667, help="Module ID (default: 667)")
argparser.add_argument("--position", type=safe_position_mm,
                       help="Measured Y position in mm; bypasses saved pixel positions")
args = argparser.parse_args()

tune_start = args.start
tune_midpoint = args.midpoint
tune_end = args.end
date = args.date
row = args.row
col = args.col

fine_ranges = np.arange(tune_start, tune_midpoint, -1)
coarse_ranges = np.arange(tune_midpoint, tune_end, -5)

ranges = np.concatenate((fine_ranges, coarse_ranges, [0.0]))

# load pixel position
if args.position is not None:
    pixel_pos = args.position
else:
    try:
        pixel_data = load_pixel_positions(f"./outputs/{args.moduleid}/pixel_positions.json")
    except (ValueError, OSError) as exc:
        argparser.error(str(exc))
    if f"r{row}c{col}" not in pixel_data["pixels"]:
        print(f"Error: Pixel r{row}c{col} not found in pixel_positions.json")
        sys.exit(1)
    
    pixel_pos = pixel_data["pixels"][f"r{row}c{col}"]["position_y_mm"]["TOT1"]

for tune in ranges:
    if tune < 0:
        print(f"Tune {tune} is too small!! You might break something!")
        break
    
    if not 0 <= pixel_pos < TRAVEL_MAX_MM[1]:
        print(f"Position {pixel_pos} is outside 0 <= Y < {TRAVEL_MAX_MM[1]:g} mm!! You might break something!")
        break

    command = f"python3 dy_laser_self_trigger_standalone_v12.py   --kcu 192.168.0.10   --rb 0   --module 1   --moduleid 667   --etroc-pos 1   --dac-mode baseline-offset --baseline-yaml /home/daq/timing_daq/module_test_sw/results/667/2026-08-12-15-49-10/module_667_etroc_1_baseline_auto.yaml   --l1a-delay 36   --pixel-mode selected  --max-events 20000  --read-interval 0.002  --event-target-source event_cnt   --print-every 10   --monitor-every 10 --dac-offset 20 --output-dir laser_self_trigger/{date}/Ext_doublePulse_125ns_offset20_230V_tune{tune}_r{row}c{col}_{pixel_pos}mm_selected --row {row} --col {col} --move {pixel_pos} --tune {tune}"
    
    os.system(command)
    
    cd = f"cd ./laser_self_trigger/{date}/Ext_doublePulse_125ns_offset20_230V_tune{tune}_r{row}c{col}_{pixel_pos}mm_selected"
    analysis = f"python3 ../../l1diff0_check_final_with_deltatot_update.py events.root --require-selected-pixel --row {row} --col {col} --pulse-gap-ns 125 --fit-bins 19 --cal-lo 160 --cal-hi 200 --tot-lo 0 --tot-hi 300 --toa-lo 0 --toa-hi 1000 --max-delta-tot 5;"
    
    os.system(cd + ";" + analysis)
    os.system("cd -")

