from pylablib.devices import Thorlabs
import time
import argparse
from laser_homing import (AXIS_CHANNELS, HOMING_FILE, MAX_VELOCITY_MM_S, configure_velocity,
                          record_home, require_enabled, require_homed, require_motion_ready)
from motion_safety import positive_timeout, safe_position_mm
import os
import sys

# os.system("export $PYTHON_PATH='/home/daq/LabInstrumentControl/3D_integration_setup/'")

steps_per_mm = 409600

def move_to(stage, value):
    target_mm = int(value)
    target_pos = int(target_mm * steps_per_mm)
    stage.move_to(target_pos)
    wait_for_motor(stage)

def move_by(stage, value):
    target_mm = int(value)
    target_pos = int(target_mm * steps_per_mm)
    stage.move_by(target_pos)
    wait_for_motor(stage)

def wait_for_motor(stage):
    status = stage.get_status()
    while status[0]=="moving_bk" or status[0]=="moving_fw":
        print(f"Waiting for the motor to go {status[0].split('_')[1]}")
        time.wait(1)

# parser = argparse.ArgumentParser(description="Thorlabs BSC20x and MLJ050 Stage Control CLI")
parser = argparse.ArgumentParser(description="Thorlabs MLJ050 Stage Control CLI")
parser.add_argument("--port", default="auto", help="Serial port (default: detect the single USB APT controller)")
parser.add_argument("--home", action="store_true", help="Home the stage before moving")
parser.add_argument("--inspect", action="store_true", help="Read identity, position, status and velocity without moving")
parser.add_argument("--move_by", type=safe_position_mm, default = "", help="Absolute target in mm (0 <= position < 150)")
parser.add_argument("--move_to", type=safe_position_mm, default = "", help="Absolute target in mm (0 <= position < 150)")
args = parser.add_mutually_exclusive_group()
# axis.add_argument("--channel", type=int, choices=(1, 2), help="Channel number (1=Y, 2=X; default 1)")
# axis.add_argument("--axis", choices=sorted(AXIS_CHANNELS), help="Axis name instead of --channel")
# parser.add_argument("--timeout", type=positive_timeout, default=60.0)

Thorlabs.list_kinesis_devices()
stage = Thorlabs.KinesisMotor(args.port) # ("/dev/ttyUSB1")

if args.inspect:
    # print("Status: ", stage.get_status())
    print("Device info: ", stage.get_device_info())
    print("Full status: ", stage.get_full_status())
    print("Velocity: ", stage.get_velocity())

if args.move_to != "":
    print("Moving to {args.move_to}...")
    move_to(stage, args.move_to)

if args.move_by != "":
    print("Moving by {args.move_by}...")
    move_by(stage, args.move_to)

if args.home:
    print("Moving home...")
    move_to(stage, 0)







