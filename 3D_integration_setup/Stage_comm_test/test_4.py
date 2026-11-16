import serial
import time
import thorlabs_apt_protocol as apt
import pdb

PORT = "/dev/ttyUSB1" # Replace with your assigned port

# 1. Open serial port with RTS/CTS enabled
port = serial.Serial(PORT, baudrate=115200, rtscts=True, timeout=5)

# 2. Mandatory Linux FTDI wake-up toggle (True -> flush -> False)
port.rts = True
port.reset_input_buffer()
port.reset_output_buffer()
port.rts = False
time.sleep(3)

# pdb.set_trace()

# 3. Send wake-up packet (dest=0x50 for MLJ050/MLJ150/MLJ250 integrated USB)
port.write(apt.hw_no_flash_programming(source=1, dest=0x50))
time.sleep(3)

# 4. Request hardware info to verify communication
port.write(apt.hw_req_info(source=1, dest=0x50))
unpacker = apt.Unpacker(port)

for msg in unpacker:
    print("Connected:", msg)
    # break

# pdb.set_trace()

# 5. Enable the motor channel (Channel 1)
port.write(apt.mod_set_chanenablestate(source=1, dest=0x50, chan_ident=1, enable_state=1))
time.sleep(3)

# 6. Home the Lab Jack (Move to 0 mm)
print("Homing Lab Jack...")
response = port.write(apt.mot_move_home(source=1, dest=0x50, chan_ident=1))
time.sleep(3)

print("Homing response: ", response)

# Wait for homing completion message (mot_move_homed)
for msg in unpacker:
    if msg.msg == "mot_move_homed":
        print("Homing complete!")
        break

# 7. Move to an absolute Z height
# MLJ150 / MLJ250 scaling: 409,600 microsteps per mm (e.g., 5.0 mm = 2,048,000)
target_mm = -5000.0
steps_per_mm = 409600
target_pos = int(target_mm * steps_per_mm)

print(f"Moving to {target_mm} mm ({target_pos} counts)...")
response = port.write(apt.mot_move_absolute(source=1, chan_ident=1, position=target_pos, dest=0x50))
print(response)
print(unpacker)

for msg in unpacker:
    # pdb.set_trace()
    # print(msg)
    # print(msg.msg)
    # for i in dir(msg):
    #     print(i)
    #     print(msg[i])
    #     print()
    # print(msg.keys())
    if msg.msg == "mot_move_completed":
        print("Move complete! Final status:", msg)
        break

port.close()
