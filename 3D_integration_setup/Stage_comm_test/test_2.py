from pylablib.devices import Thorlabs

stage = Thorlabs.KinesisMotor("/dev/ttyUSB1", "0x50")
print(stage.get_device_info())