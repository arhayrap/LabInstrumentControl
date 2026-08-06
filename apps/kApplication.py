'''

Terminal application for Keithley 2410 control.

Available commands:

vmode           Selects the voltage source mode.
imode           Selects the current source mode.
vfixed          Sets voltage source mode to fixed.
vrange{X}       Sets voltage source range in Volts. Use vrange1000 for -100 V.
icomp{X}        Sets current compliance in Amps when sourcing voltage.
vprot{X}        Sets source voltage protection level in Volts.
hvsetup         Configures high-voltage source: fixed mode, 1000 V range, 10 uA compliance.
hvsetup-{X}     Same as hvsetup, but with given current compliance in Amps.
vmeas           Measures the voltage and prints it.
imeas           Measures the current and prints it.
vsetcrude{X}    Sets the voltage immediately to 'X' Volts.
isetcrude{X}    Sets the current immediately to 'X' Amperes.
reset           Resets the Keithley.
cls             Clears status and error registers.
vramp{X}        Ramps the voltage to 'X' at 10 Volts per second.
vramp{X}-{Y}    Ramps the voltage to 'X' Volts at 'Y' Volts per second.
vrampd          Ramps the voltage down to 0 at default speed.
vrampd{X}       Ramps the voltage down to 0 at 'X' Volts per second.
on              Turns the output ON.
off             Turns the output OFF.
status          Prints useful Keithley status information.
idn             Reads Keithley identity.
err             Reads Keithley errors.
quit/exit/q     Ramps down the voltage to 0, turns output off, exits the terminal app.

Samvel Aghavelyan
01Jul2026

latest change: 06Aug2026
'''


import argparse
import re
from classes.Keithley2410_class import Keithley2410


NUMBER_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


'''terminal helper functions'''

def parseCommand(user_input: str):
    '''Parses the command that the user typed.'''
    command = user_input.strip().lower()

    if command == "":
        return None, {}

    if command in ["help", "h", "?"]:
        return "help", {}

    if command in ["quit", "exit", "q"]:
        return "quit", {}

    if command in [
        "vmode",
        "imode",
        "vfixed",
        "reset",
        "cls",
        "vmeas",
        "imeas",
        "on",
        "off",
        "status",
        "idn",
        "err",
        "hvsetup",
        "local"
    ]:
        return command, {}

    match = re.fullmatch(rf"vsetcrude({NUMBER_PATTERN})", command)
    if match:
        return "vsetcrude", {
            "voltage": float(match.group(1)),
        }

    match = re.fullmatch(rf"isetcrude({NUMBER_PATTERN})", command)
    if match:
        return "isetcrude", {
            "current": float(match.group(1)),
        }

    match = re.fullmatch(rf"vrange({NUMBER_PATTERN})", command)
    if match:
        return "vrange", {
            "voltage_range": float(match.group(1)),
        }

    match = re.fullmatch(rf"icomp({NUMBER_PATTERN})", command)
    if match:
        return "icomp", {
            "current_limit": float(match.group(1)),
        }

    match = re.fullmatch(rf"vprot({NUMBER_PATTERN}|max)", command)
    if match:
        voltage_limit = match.group(1)
        if voltage_limit != "max":
            voltage_limit = float(voltage_limit)
        else:
            voltage_limit = "MAX"
        return "vprot", {
            "voltage_limit": voltage_limit,
        }

    match = re.fullmatch(rf"hvsetup-({NUMBER_PATTERN})", command)
    if match:
        return "hvsetup", {
            "current_limit": float(match.group(1)),
        }

    match = re.fullmatch(rf"vramp({NUMBER_PATTERN})(?:-({NUMBER_PATTERN}))?", command)
    if match:
        speed = match.group(2)
        return "vramp", {
            "v_final": float(match.group(1)),
            "speed": float(speed) if speed is not None else None,
        }

    match = re.fullmatch(rf"vrampd(?:({NUMBER_PATTERN}))?", command)
    if match:
        speed = match.group(1)
        return "vrampd", {
            "speed": float(speed) if speed is not None else None,
        }

    return "unknown", {
        "command": command,
    }


def executeCommand(keithley, command: str, parameters: dict, default_ramp_down_speed: float):
    '''Executes the command that the user typed.'''

    if command is None:
        return True

    if command == "help":
        keithley.kApplicationHelp()

    elif command == "quit":
        return False

    elif command == "local":
        keithley.kSetLocalMode()
        print("Local mode activated.")

    elif command == "vmode":
        keithley.kSetVoltageMode()
        print("Voltage source mode selected.")

    elif command == "imode":
        keithley.kSetCurrentMode()
        print("Current source mode selected.")

    elif command == "vfixed":
        keithley.kSetVoltageSourceModeFixed()
        print("Voltage source mode fixed selected.")

    elif command == "reset":
        keithley.kReset()
        print("Keithley reset complete.")

    elif command == "cls":
        keithley.kClearStatus()
        print("Status and error registers cleared.")

    elif command == "on":
        keithley.kSetOutput(1)
        print("Output on.")

    elif command == "off":
        keithley.kSetOutput(0)
        print("Output off.")

    elif command == "vsetcrude":
        voltage = parameters["voltage"]
        keithley.kSetVoltageCrude(voltage)
        print(f"Voltage set to {voltage} V.")

    elif command == "isetcrude":
        current = parameters["current"]
        keithley.kSetCurrentCrude(current)
        print(f"Current set to {current} A.")

    elif command == "vrange":
        voltage_range = parameters["voltage_range"]
        keithley.kSetVoltageSourceRangeAuto(False)
        keithley.kSetVoltageSourceRange(voltage_range)
        print(f"Voltage source range set to {voltage_range} V.")

    elif command == "icomp":
        current_limit = parameters["current_limit"]
        keithley.kSetCurrentCompliance(current_limit)
        print(f"Current compliance set to {current_limit} A.")

    elif command == "vprot":
        voltage_limit = parameters["voltage_limit"]
        keithley.kSetVoltageProtection(voltage_limit)

    elif command == "hvsetup":
        current_limit = parameters.get("current_limit", 10e-6)
        keithley.kConfigureVoltageSource(
            voltage_range=1000,
            current_compliance=current_limit,
            voltage_protection="MAX",
            auto_current_range=True,
        )
        print("High-voltage voltage-source setup complete.")
        print("Voltage range:       1000 V")
        print(f"Current compliance: {current_limit} A")

    elif command == "vramp":
        v_final = parameters["v_final"]
        speed = parameters["speed"]
        if speed is None:
            speed = 10
        print(f"Ramping to {v_final} V at {speed} V/s.")
        keithley.kRamp(v_final=v_final, v_per_s=speed)
        print(f"Reached {v_final} V.")

    elif command == "vrampd":
        speed = parameters["speed"]
        if speed is None:
            speed = default_ramp_down_speed
        print(f"Ramping down to 0 V at {speed} V/s.")
        keithley.kRamp(v_final=0, v_per_s=speed, delta_t_hardware=0)
        print("Reached 0 V.")

    elif command == "vmeas":
        voltage = keithley.kMeasureVoltage()
        print(f"Voltage: {voltage:.8g} V")

    elif command == "imeas":
        current = keithley.kMeasureCurrent()
        print(f"Current: {current:.8g} A")

    elif command == "status":
        keithley.kPrintStatus()

    elif command == "idn":
        print(keithley.kReadIdentity())

    elif command == "err":
        for error in keithley.kReadAllErrors():
            print(error)

    elif command == "unknown":
        print(f"Unknown command: {parameters['command']}")
        print("Type help to see available commands.")

    return True


def main():
    '''Terminal App.'''

    parser = argparse.ArgumentParser(description="Keithley 2410 terminal application.")

    parser.add_argument(
        "--port",
        default="ASRL/dev/ttyS0::INSTR",
        help="PyVISA port of the Keithley.",
    )

    parser.add_argument(
        "--baud-rate",
        type=int,
        default=9600,
        help="RS-232 baud rate.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=5000,
        help="Timeout in ms.",
    )

    parser.add_argument(
        "--default-ramp-down-speed",
        type=float,
        default=20.0,
        help="Default ramp-down speed in V/s.",
    )

    args = parser.parse_args()

    keithley = None

    try:
        print("Connecting to Keithley 2410...")
        keithley = Keithley2410(port=args.port, baud_rate=args.baud_rate, timeout=args.timeout)
        print("Connected.")
        print("Type 'help' to see the available commands.")
        print()

        try:
            print("Keithley identity:")
            print(keithley.kReadIdentity())
            print()
        except Exception:
            print("Could not read identity, but the connection was created.")
            print()

        while True:
            try:
                user_input = input("k2410> ")

                command, parameters = parseCommand(user_input)

                keep_running = executeCommand(
                    keithley,
                    command,
                    parameters,
                    default_ramp_down_speed=args.default_ramp_down_speed,
                )

                if not keep_running:
                    break

            except KeyboardInterrupt:
                print()
                print("Keyboard interrupt.")
                print("Use vrampd to ramp down, off to turn off the output, or q to quit.")

            except Exception as error:
                print(f"Error: {error}")
                try:
                    print("Keithley errors:")
                    for keithley_error in keithley.kReadAllErrors():
                        print(keithley_error)
                except Exception:
                    pass

    finally:
        if keithley is not None:
            print()
            print("Safe shutdown.")

            try:
                keithley.kSafeShutdown()
                print("Output off.")
            except Exception as error:
                print(f"Problem during safe shutdown: {error}")

            try:
                print("Keithley errors:")
                for keithley_error in keithley.kReadAllErrors():
                    print(keithley_error)
            except Exception:
                pass

        if keithley is not None:
            keithley.kClose()

        print("Connection closed.")


if __name__ == "__main__":
    main()
