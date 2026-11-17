from pylablib.devices import Thorlabs
import time
import argparse
from laser_homing import (AXIS_CHANNELS, HOMING_FILE, MAX_VELOCITY_MM_S, configure_velocity,
                          record_home, require_enabled, require_homed, require_motion_ready)
from motion_safety import positive_timeout, safe_position_mm
import os
import sys
import serial
import pdb

# os.system("export $PYTHON_PATH='/home/daq/LabInstrumentControl/3D_integration_setup/'")

steps_per_mm = 1024000 # 819200 # 409600
max_z = 50.8 * steps_per_mm

def move_to(stage, value):
    target_mm = float(value)
    target_pos = target_mm * steps_per_mm
    stage.move_to(target_pos)
    wait_for_motor(stage, target_pos)

def move_by(stage, value):
    target_mm = float(value)
    target_pos = target_mm * steps_per_mm
    stage.move_by(target_pos)
    if stage.get_position() + target_pos >= max_z:
        final_destination = max_z
    elif stage.get_position() + target_pos < 0:
        final_destination = 0
    else:
        final_destination = stage.get_position() + target_pos
    print(final_destination, stage.get_position() + target_pos)
    wait_for_motor(stage, final_destination)

def wait_for_motor(stage, destination): # destination in step units
    status = stage.get_position() # stage.get_status()
    old_status = -1000
    while status != old_status: # destination: # status[0]=="moving_bk" or status[0]=="moving_fw":
        print(f"Currently {status}, moving to: {destination}.")
        print(f"Waiting for the motor to go {stage.get_status()[0].split('_')[-1]}.")
        old_status = status
        status = stage.get_position()
        time.sleep(5)

def update_port(port):
    ser = serial.Serial(port, baudrate=9600, timeout=1)
    ser.close()

def homing(stage):
    print("Now homing")
    stage.move_to(0)
    stage.home(sync=True)
    wait_for_motor(stage, 0)

# parser = argparse.ArgumentParser(description="Thorlabs BSC20x and MLJ050 Stage Control CLI")
parser = argparse.ArgumentParser(description="Thorlabs MLJ050 Stage Control CLI")
parser.add_argument("--port", default="auto", help="Serial port (default: detect the single USB APT controller)")
parser.add_argument("--home", action="store_true", help="Home the stage before moving")
parser.add_argument("--inspect", action="store_true", help="Read identity, position, status and velocity without moving")
parser.add_argument("--move_by", default = "", help="Absolute target in mm (0 <= position < 150)")
parser.add_argument("--move_to", default = "", help="Absolute target in mm (0 <= position < 150)")
args = parser.parse_args()
# axis.add_argument("--channel", type=int, choices=(1, 2), help="Channel number (1=Y, 2=X; default 1)")
# axis.add_argument("--axis", choices=sorted(AXIS_CHANNELS), help="Axis name instead of --channel")
# parser.add_argument("--timeout", type=positive_timeout, default=60.0)

if __name__ == "__main__":
    
    print(Thorlabs.list_kinesis_devices())
    update_port(args.port)
    
    connection_status = False
    while connection_status is False:
        try:
            update_port(args.port)
            stage = Thorlabs.KinesisMotor(args.port) # , scale = (steps_per_mm, 1, 1)) # , is_rack_system=True) # ("/dev/ttyUSB1")
            print(f"Connection with {stage.get_device_info()} is established.")
            connection_status = True
            stage.home(sync=True)
        except:
            print("Connection with the device has failed, trying again.")
        # exit()
    # pdb.set_trace()
    if args.home:
        homing(stage)
    
    try:
        try:
            if args.inspect:
                # print("Status: ", stage.get_status())
                print("Device info: ", stage.get_device_info())
                print("Full status: ", stage.get_full_status())
                print("Velocity: ", stage.setup_velocity())
        except:
            print("Device inspect failed.")
            stage.close()
    
        try:
            if args.move_to != "":
                print(f"Moving to {args.move_to}...")
                move_to(stage, args.move_to)
        except:
            print("Moving to operation failed.")
            stage.close()
    
        try:
            if args.move_by != "":
                print(f"Moving by {args.move_by}...")
                move_by(stage, args.move_by)
        except:
            print("Moving by operation failed.")
            stage.close()
    
        try:
            if args.home:
                print("Moving home...")
                move_to(stage, 0)
        except:
            print("Moving home operation failed.")
            stage.close()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        stage.close()
    finally:
        print("Moving operations by Z axis are complete.")
        stage.close()
    