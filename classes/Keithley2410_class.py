'''
Utilities for Keithley 2410 (RS-232 connection) control using python (Keithley is defined here as an object).
These are custom-defined functions for easier and more intuitive use of serial
interface commands. This is library/object definition for a Keithley2410.

Samvel Aghavelyan
29Jun2026
'''


import pyvisa
import time
import numpy as np


class Keithley2410:
    '''Keithley 2410 pyvisa object instance.'''

    def __init__(self, port="ASRL/dev/ttyS0::INSTR", baud_rate=9600, timeout=6000000, rm=None):
        '''Creates the pyvisa Keithley instance with the resource manager. <br>
        If rm is not provided, a new pyvisa.ResourceManager() will be created. <br>
        Change port to your Keithley 2410's pyvisa address.'''

        self.rm = rm if rm is not None else pyvisa.ResourceManager()
        self.keithley = self.rm.open_resource(port)

        # serial communication settings
        self.keithley.baud_rate = baud_rate
        self.keithley.data_bits = 8
        self.keithley.parity = pyvisa.constants.Parity.none
        self.keithley.stop_bits = pyvisa.constants.StopBits.one
        self.keithley.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
        self.keithley.timeout = timeout

        # keithley 2410 RS-232 line endings
        self.keithley.write_termination = "\r"
        self.keithley.read_termination = "\r"

        # sets first number of the output the voltage, the second will be the current and so on
        self.keithley.write(":FORM:ELEM VOLT,CURR,RES,TIME,STAT")


    # ----------------------------------------
    # SCPI-command-requiring methods
    # ----------------------------------------
    def kWrite(self, command: str):
        '''Sends one SCPI command to the Keithley.'''

        self.keithley.write(command)

    def kQuery(self, command: str):
        '''Sends one SCPI query to the Keithley and returns the response.'''

        return self.keithley.query(command).strip()



    # ----------------------------------------
    # General functions
    # ----------------------------------------
    def kClose(self):
        '''Closes the keithley and resource manager.'''
        self.kSetLocalMode()
        self.keithley.close()
        self.rm.close()

    def kSetMode(self, mode: str):
        '''Expected input: "voltage" or "current". Uppercase/lowercase letters will not cause an error.'''
        if mode.upper() == "VOLTAGE":
            self.keithley.write(":SOUR:FUNC VOLT")
        elif mode.upper() == "CURRENT":
            self.keithley.write(":SOUR:FUNC CURR")
        else:
            print("Wrong parameter to kSetMode(). Expected: \"voltage\" or \"current\".")

    def kSetOutput(self, state: bool):
        '''Expected input: 0/False or 1/True.'''
        if state in [True, False, 0, 1]:
            self.keithley.write(f":OUTP {int(state)}")
        else:
            print("Wrong parameter to kSetOutput(). Expected: 0/False or 1/True.")

    def kOutputOn(self):
        '''Turns the output on.'''
        self.kSetOutput(True)

    def kOutputOff(self):
        '''Turns the output off.'''
        self.kSetOutput(False)

    def kSetLocalMode(self):
        '''Sets the mode from remote to local: activates front panel buttons.'''
        self.keithley.write(":SYST:LOC")

    def kReset(self):
        '''Resets the whole instrument to predefined state.'''
        self.keithley.write("*RST")
        time.sleep(0.5)

        # sets first number of the output the voltage, the second will be the current
        self.keithley.write(":FORM:ELEM VOLT,CURR,RES,TIME,STAT")

    def kClearStatus(self):
        '''Clears the status and error registers.'''
        self.keithley.write("*CLS")

    def kSafeShutdown(self, v_per_s: float = 20.0):
        '''Ramps down to 0 Volts and turns the output off.'''
        try:
            self.kRampDown(v_per_s=v_per_s)
        finally:
            self.kSetOutput(0)



    # ----------------------------------------
    # Voltage configuring commands
    # ----------------------------------------
    def kSetVoltageMode(self):
        '''Sets the Keithley to voltage source mode.'''
        self.kSetMode("voltage")

    def kSetVoltageCrude(self, voltage: float):
        '''Set voltage of the output (in Volts) IMMEDIATELY. Does not automatically turn on the output.'''
        self.keithley.write(f":SOUR:VOLT {voltage}")

    def kSetVoltageSourceRange(self, voltage_range: float):
        '''Sets the voltage source range in Volts. For -100 V use 1000.'''
        self.keithley.write(f":SOUR:VOLT:RANG {voltage_range}")

    def kSetVoltageSourceModeFixed(self):
        '''Sets voltage source mode to fixed level mode.'''
        self.keithley.write(":SOUR:VOLT:MODE FIXED")

    def kSetVoltageSourceRangeAuto(self, state: bool):
        '''Turns voltage source auto range on or off.'''
        self.keithley.write(f":SOUR:VOLT:RANG:AUTO {int(state)}")

    def kSetVoltageCompliance(self, voltage_limit: float):#
        '''Sets voltage compliance in Volts when sourcing current.'''
        self.keithley.write(f":SENS:VOLT:PROT {voltage_limit}")

    def kSetVoltageProtection(self, voltage_limit):
        '''Sets source voltage protection level. voltage_limit can be 20/40/100/200/300/400/500 or "NONE".'''
        if voltage_limit in [20, 40, 100, 200, 300, 400, 500, "NONE"]:
            self.keithley.write(f":SOUR:VOLT:PROT:LEV {voltage_limit}")
            print(f"Voltage protection set to {voltage_limit}.")
            return
        else:
            self.keithley.write(f":SOUR:VOLT:PROT:LEV {voltage_limit}")
            print(f"Provided limit is not in expected values so")
            print(f"voltage protection is set to {self.keithley.query(f":SOUR:VOLT:PROT:LEV?")} V.")

    def kSetSenseVoltageRange(self, voltage_range: float):
        '''Sets the voltage measurement range in Volts.'''
        self.keithley.write(f":SENS:VOLT:RANG {voltage_range}")

    def kSetSenseVoltageRangeAuto(self, state: bool):
        '''Turns voltage measurement auto range on or off.'''
        self.keithley.write(f":SENS:VOLT:RANG:AUTO {int(state)}")

    def kSetMeasureFunctionVoltage(self):
        '''Sets the measurement function to DC voltage.'''
        self.keithley.write(":SENS:FUNC 'VOLT:DC'")

    def kConfigureVoltageSource(
            self, 
            voltage_range: float = 1000, 
            current_compliance: float = 10e-6,
            current_range: float = None,
            voltage_protection="MAX",
            auto_current_range: bool = True
        ):
        '''Configures Keithley as voltage source with safe high-voltage settings.'''

        self.kClearStatus()
        self.kSetVoltageMode()
        self.kSetVoltageSourceModeFixed()
        self.kSetVoltageSourceRangeAuto(False)
        self.kSetVoltageSourceRange(voltage_range)
        self.kSetVoltageProtection(voltage_protection)
        self.kSetMeasureFunctionCurrent()
        self.kSetCurrentCompliance(current_compliance)

        if auto_current_range:
            self.kSetSenseCurrentRangeAuto(True)

        elif current_range is not None:
            self.kSetSenseCurrentRange(current_range)

    def kRamp(self, v_final: float, v_per_s: float = 10, v_step=1, stop_on_error: bool = True, delta_t_hardware=0.0328): # needs rewriting if accurate v_per_s is needed
        '''Changes the voltage gradually at v_per_s (at least theoretically) till reaches v_final.<br>
        <br>
        !!! Note !!!
        <br>
        ●   Actual v_per_s will depend on the v_step you give. The problem is the hardware (PC) delay (python is slow).<br>
        ●   Function default parameters (delta_t_hardware, v_step) are chosen for a PC with Intel(R) Xeon(R) W-2225 CPU @ 4.10GHz.<br>'''
        v_per_s = abs(v_per_s)
        v_step = abs(v_step)
        v_initial = self.kReadSetVoltage()
        v_diff = v_final - v_initial

        if abs(v_diff) < 1e-12:
            self.kSetVoltageCrude(v_final)
            return

        k_step = np.sign(v_diff)
        n_steps = int(np.floor(np.abs(v_diff / v_step)))
        t_delay = np.abs(v_step / v_per_s) - delta_t_hardware
        # t_delay = np.abs(v_step / v_per_s)

        for i in range(1, n_steps + 1):
            v_now = v_initial + i * k_step * np.abs(v_step)
            self.kSetVoltageCrude(v_now)
            time.sleep(t_delay)
            # print(t_delay)
            if stop_on_error:
                error = self.kReadErrors()

                if not error.startswith("0"):
                    raise RuntimeError(f"Keithley error during ramp at {v_now} V: {error}")

        self.kSetVoltageCrude(v_final)                    # ensuring that the final voltage is exactly v_final

    def kRampDown(self, v_per_s: float = 5.0, v_step=0.5):
        '''Changes the voltage gradually at v_per_s till reaches 0 Volts.'''
        self.kRamp(v_final=0, v_per_s=v_per_s, v_step=v_step)



    # -------------------------------------------------------
    # Current configuring commands (most are not tested yet) 
    # -------------------------------------------------------
    def kSetCurrentMode(self):
        '''Sets the Keithley to current source mode.'''
        self.kSetMode("current")

    def kSetCurrentCrude(self, current: float):
        '''Set current of the output (in Amps) IMMEDIATELY. Does not automatically turn on the output.'''
        self.keithley.write(f":SOUR:CURR {current}")

    def kSetCurrentSourceModeFixed(self):
        '''Sets current source mode to fixed level mode.'''
        self.keithley.write(":SOUR:CURR:MODE FIXED")

    def kSetCurrentSourceRange(self, current_range: float):
        '''Sets the current source range in Amps.'''
        self.keithley.write(f":SOUR:CURR:RANG {current_range}")

    def kSetCurrentSourceRangeAuto(self, state: bool):
        '''Turns current source auto range on or off.'''
        self.keithley.write(f":SOUR:CURR:RANG:AUTO {int(state)}")

    def kSetCurrentCompliance(self, current_limit: float):#
        '''Sets current compliance in Amps when sourcing voltage.'''
        self.keithley.write(f":SENS:CURR:PROT {current_limit}")

    def kSetSenseCurrentRange(self, current_range: float):
        '''Sets the current measurement range in Amps.'''
        self.keithley.write(f":SENS:CURR:RANG {current_range}")

    def kSetSenseCurrentRangeAuto(self, state: bool):
        '''Turns current measurement auto range on or off.'''
        self.keithley.write(f":SENS:CURR:RANG:AUTO {int(state)}")

    def kSetMeasureFunctionCurrent(self):
        '''Sets the measurement function to DC current.'''
        self.keithley.write(":SENS:FUNC 'CURR:DC'")



    # ----------------------------------------
    # Reading functions
    # ----------------------------------------
    def kReadOutputState(self):
        '''Returns
        \n0 - output is off,
        \n1 - output is on.'''
        response = self.keithley.query(":OUTP?")
        return int(response)

    def kReadMode(self):
        '''Reads the source mode of the Keithley.'''
        return self.keithley.query(":SOUR:FUNC?").strip()

    def kReadVoltageSourceMode(self):
        '''Reads the voltage source mode.'''
        return self.keithley.query(":SOUR:VOLT:MODE?").strip()

    def kReadVoltageSourceRange(self):
        '''Reads the voltage source range in Volts.'''
        response = self.keithley.query(":SOUR:VOLT:RANG?")
        return float(response)

    def kReadCurrentCompliance(self):
        '''Reads current compliance in Amps.'''
        response = self.keithley.query(":SENS:CURR:PROT?")
        return float(response)

    def kReadVoltageProtection(self):
        '''Reads source voltage protection level in Volts.'''
        response = self.keithley.query(":SOUR:VOLT:PROT:LEV?")
        return float(response)

    def kReadSetVoltage(self):
        '''Reads the voltage value that the Keithley is set to output.'''
        response = self.keithley.query(":SOUR:VOLT?")
        return float(response)

    def kReadIdentity(self):
        '''Reads the Keithley identifiers. You can use mostly to test communication.'''
        return self.keithley.query("*IDN?").strip()

    def kReadErrors(self):
        '''Reads one Keithley error from the error queue.'''
        return self.keithley.query(":SYST:ERR?").strip()

    def kReadAllErrors(self, max_errors: int = 20):
        '''Reads the whole Keithley error queue.'''
        errors = []
        for i in range(max_errors):
            error = self.kReadErrors()
            errors.append(error)

            if error.startswith("0"):
                break

        return errors

    def kPrintStatus(self):
        '''Prints useful Keithley status information.'''

        print("Identity:", self.kReadIdentity())
        print("Output state:", bool(self.kReadOutputState()))
        print("Source mode:", self.kReadMode())
        print("Voltage source mode:", self.kReadVoltageSourceMode())
        print("Voltage set:", self.kReadSetVoltage(), "V")
        print("Voltage source range:", self.kReadVoltageSourceRange(), "V")
        print("Voltage protection:", self.kReadVoltageProtection(), "V")
        print("Current compliance:", self.kReadCurrentCompliance(), "A")
        print("Errors:")

        for error in self.kReadAllErrors():
            print("   ", error)



    # ----------------------------------------
    # Measurement functions
    # ----------------------------------------
    def kMeasureVoltage(self, t_wait: float = 0.0):
        '''Measures the voltage. Waits t_wait seconds, if needed, before taking the measurement.'''

        self.keithley.write(f":SOUR:DEL {t_wait}")           # waits t_wait seconds before measuring the voltage (can use for stabilising)
        response = self.keithley.query(":MEAS:VOLT?")        # this is a string with numbers separated by comma
        return float(response.split(",")[0])                 # the first one of the numbers is the voltage

    def kMeasureCurrent(self, t_wait: float = 0.0):
        '''Measures the current.'''

        self.keithley.write(f":SOUR:DEL {t_wait}")
        response = self.keithley.query(":MEAS:CURR?")
        return float(response.split(",")[1])                 # the second one of the numbers is the current



    # ----------------------------------------
    # kApplication functions
    # ----------------------------------------
    @staticmethod
    def kApplicationHelp():
        '''Prints the available terminal commands.'''

        print(
            ("Available commands:\n"),
            ("vmode           Selects the voltage source mode.\n"), 
            ("imode           Selects the current source mode.\n"),
            ("vfixed          Sets voltage source mode to fixed.\n"),
            ("vrange{X}       Sets voltage source range in Volts. Use vrange1000 for -100 V.\n"),
            ("icomp{X}        Sets current compliance in Amps when sourcing voltage.\n"),
            ("vprot{X}        Sets source voltage protection level in Volts.\n"),
            ("hvsetup         Configures high-voltage source: fixed mode, 1000 V range, 10 uA compliance.\n"),
            ("hvsetup-{X}     Same as hvsetup, but with given current compliance in Amps.\n"),
            ("vmeas           Measures the voltage and prints it.\n"),
            ("imeas           Measures the current and prints it.\n"),
            ("vsetcrude{X}    Sets the voltage immediately to 'X' Volts.\n"),
            ("isetcrude{X}    Sets the current immediately to 'X' Amperes.\n"),
            ("reset           Resets the Keithley.\n"),
            ("cls             Clears status and error registers.\n"),
            ("vramp{X}        Ramps the voltage to 'X' at 10 Volts per second.\n"),
            ("vramp{X}-{Y}    Ramps the voltage to 'X' Volts at 'Y' Volts per second.\n"),
            ("vrampd          Ramps the voltage down to 0 at default speed.\n"),
            ("vrampd{X}       Ramps the voltage down to 0 at 'X' Volts per second.\n"),
            ("on              Turns the output ON.\n"),
            ("off             Turns the output OFF.\n"),
            ("status          Prints useful Keithley status information.\n"),
            ("idn             Reads Keithley identity.\n"),
            ("err             Reads Keithley errors.\n"),
            ("quit/exit/q     Ramps down the voltage to 0, turns output off, exits the terminal app.\n"),
            )
