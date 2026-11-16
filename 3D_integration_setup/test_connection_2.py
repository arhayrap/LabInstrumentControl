import usb.core
import usb.util

dev = usb.core.find(
    idVendor=0x05ff,
    idProduct=0x1023
)

if dev is None:
    print("Device not found")
else:
    print("Device found")

    dev.set_configuration()
    print("Configuration successful")

    cfg = dev.get_active_configuration()

    for intf in cfg:
        print("Interface:", intf.bInterfaceNumber)

        try:
            dev.detach_kernel_driver(intf.bInterfaceNumber)
        except Exception as e:
            print("Detach:", e)
        try:
            dev.claim_interface(intf.bInterfaceNumber)
            print("Interface claimed successfully")
        except Exception as e:
            print("Claim failed:", repr(e))
