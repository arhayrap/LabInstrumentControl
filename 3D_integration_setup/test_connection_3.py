import usb.core

dev = usb.core.find(
    idVendor=0x05ff,
    idProduct=0x1023
)

if dev is None:
    print("Device not found")
else:
    print("Device found")

    print("Active configuration:")
    try:
        cfg = dev.get_active_configuration()
        print(cfg)

        for intf in cfg:
            print(
                "Interface:", intf.bInterfaceNumber,
                "Class:", intf.bInterfaceClass,
                "Subclass:", intf.bInterfaceSubClass
            )

    except Exception as e:
        print("Configuration error:", repr(e))
