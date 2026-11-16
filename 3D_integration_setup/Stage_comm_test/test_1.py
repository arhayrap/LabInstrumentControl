import serial
import struct
import time

PORT = "/dev/ttyUSB1" # Change if your port is ttyUSB1, etc.

# Open port with exact Thorlabs APT specifications
ser = serial.Serial(
    port=PORT,
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    rtscts=True,   # Mandatory for Thorlabs FTDI chips
    timeout=1.0
)

# Crucial Linux FTDI fix: toggle RTS and flush buffers
ser.setRTS(True)
time.sleep(0.05)
ser.reset_input_buffer()
ser.reset_output_buffer()

# Try querying hardware info (MGMSG_HW_REQ_INFO: 0x0005) across common destination bytes
for dest in [0x50, 0x11, 0x21]:
    cmd_hw_info = struct.pack('<HBBBB', 0x0005, 0x00, 0x00, dest, 0x01)
    ser.write(cmd_hw_info)
    time.sleep(0.1)
    reply = ser.read(90) # Hardware info packet is 90 bytes
    if len(reply) > 0:
        print(f"SUCCESS on dest=0x{dest:02X}! Received {len(reply)} bytes.")
        print("Model:", reply[10:18].decode('ascii', errors='ignore').strip('\x00'))
        break
else:
    print("No response on any destination byte.")

ser.close()
