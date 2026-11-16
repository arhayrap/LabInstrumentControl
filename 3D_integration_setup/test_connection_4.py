import usb.core
import pyvisa

# 1. Find the raw USB device and reset it
# Replace with your instrument's hex Vendor ID and Product ID
dev = usb.core.find(idVendor=1535, idProduct=4131) 
if dev is not None:
    try:
        dev.reset()
        print("USB device reset successfully.")
    except usb.core.USBError as e:
        print(f"Could not reset device: {e}")

# 2. Proceed with normal PyVISA initialization
rm = pyvisa.ResourceManager()
# Use your specific resource string
inst = rm.open_resource("USB0::1535::4131::5003N60377::0::INSTR") 
print(inst.query("*IDN?"))
