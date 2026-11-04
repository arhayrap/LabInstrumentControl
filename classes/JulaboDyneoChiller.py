'''
Utilities for Teledyne Lecroy Waverunner 8000 series oscilloscope control using python.
These are custom-defined methods for easier and more intuitive use of SCPI
interface commands. This file is library/script that defines an object for
the Teledyne Lecroy Waverunner 8000 series scope.

Aram Hayrapetyan / Samvel Aghavelyan
01Oct2026 - 24Oct2026
'''

import pyvisa
import time

DEFAULT_LECROY_VISA_ADDRESS = "USB0::10893::36867::MY64060141::0::INSTR" # CHANGE !
DEFAULT_LECROY_VISA_LIBRARY_PATH = "/opt/keysight/iolibs/libktvisa32.so" # CHANGE !
SCOPE_WAVEFORM_DIR = r"C:\Users\Public\Documents\Infiniium\Waveforms" # CHANGE !


# Teledyne Lecroy Waverunner 8000 series scope
# InfiniiumScope class

class InfiniiumScope:
    '''Teledyne Lecroy Waverunner 8000 oscilloscope object.'''
    def __init__(
            self,
            visa_address=DEFAULT_LECROY_VISA_ADDRESS,
            visa_library_path=DEFAULT_LECROY_VISA_LIBRARY_PATH,
            # resource_manager=None,
            timeout=3000000,
            encoding="latin_1"
        ):
        '''Creates the pyvisa Lecroy oscilloscope instance.'''

        self.visa_address = visa_address
        self.visa_library_path = visa_library_path
        self.timeout = timeout
        self.encoding = encoding


        if visa_address is None:
            self.rm = pyvisa.ResourceManager()
        else:
            self.rm = pyvisa.ResourceManager(visa_library_path)


        self.instrument = self.rm.open_resource(visa_address)


        self.instrument.timeout = timeout
        self.instrument.encoding = encoding

        # normal SCPI line endings for USB/VISA instruments
        self.instrument.write_termination = "\n"
        self.instrument.read_termination = "\n"



    # ----------------------------------------------------------------
    # Functions that require direct SCPI commands as a string
    # ----------------------------------------------------------------
    def iWrite(self, command: str):#✅
        '''Sends one SCPI command to the oscilloscope.'''
        self.instrument.write(command)

    def iQuery(self, command: str):#✅
        '''Sends one SCPI query to the oscilloscope and returns the response.'''
        return self.instrument.query(command).strip()


########################not acquisition mode, but sampling mode. the segmented and real time ones. i guess. read more
    # ----------------------------------------------------------------
    # Acquisition commands (most start with :ACQuire).
    # ----------------------------------------------------------------
    def iSetInterpolation(self, state: int):#✅
        '''Turns interpolation on or off. <br> In plain words: the scope
        takes the real acquired sample points and calculates extra 
        smooth points between them. <br> Expected input: 0/False, 1/True, or 2/4/8/16/32.'''
        if state is None:
            print("Did not set INTERPOLATION.")
            return
        if state == 0:
            self.instrument.write(f":ACQuire:INTerpolate {int(state)}")
        elif state in [1, 2, 4, 8, 16, 32]:
            self.instrument.write(f":ACQuire:INTerpolate INT{int(state)}")
        else:
            print("WRONG PARAMETER is given to iSetInterpolation().")

    def iReadInterpolation(self):#✅
        '''Returns interpolation settings. RETURNED STRING MAY NEED FORMATTING.'''
        response = self.instrument.query(":ACQuire:INTerpolate?")
        return int(response.strip("INT"))

    def iSetAcquisitionMode(self, mode: str="SEGmented"):#✅
        '''Sets the acquisition mode. <br> Default: "SEGmented". <br> 
        Examples: "RTIMe"/"PDETect"/"HRESolution". <br> Function is defined for "SEGmented."'''
        if mode is None:
            print("Did not set ACQUISITION MODE.")
            return
        self.instrument.write(f":ACQuire:MODE {mode}")

    def iSetWhichSegmentsToSave(self, which_segments_to_save: str="ALL"):
        '''Sets saving mode to save "CURRent" or "ALL" segments.'''
        if which_segments_to_save is None:
            print("Did not set WHICH SEGMENTS TO SAVE.")
            return
        self.instrument.write(f":DISK:SEGMented {which_segments_to_save}")

    def iSetSegmentCount(self, n_segments: int):#✅
        '''Sets the number of segments/events to acquire.'''
        if n_segments is None:
            print("Did not set SEGMENT COUNT.")
            return        
        self.instrument.write(f":ACQuire:SEGMented:COUNt {int(n_segments)}")

    def iReadSegmentCount(self):#✅
        '''Reads the number of acquisition segments.'''
        response = self.instrument.query(":ACQuire:SEGMented:COUNt?")
        return int(float(response))

    def iSetSampleRate(self, sample_rate_sa_s):#✅
        '''Sets the analog sample rate in samples/second. ,br>
        ● sample_per_segment: can be an integer, or "AUTO".'''
        if sample_rate_sa_s is None:
            print("Did not set SAMPLING RATE.")
            return
        self.instrument.write(f":ACQuire:SRATe:ANALog {sample_rate_sa_s}")

    def iReadSampleRate(self):#✅
        '''Reads the analog sample rate in samples/second.'''
        response = self.instrument.query(":ACQuire:SRATe:ANALog?")
        return float(response)

    def iSetSamplePerSegment(self, sample_per_segment):#✅
        '''Sets how many samples should be acuired in one event. <br>
        ● sample_per_segment: can be an integer, or "MAX" (NOT RECOMMENDED BECAUSE CAN CAUSE CRASHES), or "AUTO".'''
        if sample_per_segment is None:
            print("Did not set SAMPLE PER SEGMENT.")
            return
        self.instrument.write(f":ACQuire:POINts:ANALog {sample_per_segment}")

    def iReadSamplePerSegment(self):#✅
        '''Reads what is set up as samples per segment. <br>
        Can return "MAX", "AUTO" or an integer [samples/s].'''
        response = self.iQuery(":ACQuire:POINts:ANALog?")
        return float(response)

    def iRun(self):#✅
        '''Starts the oscilloscope running. When the oscilloscope is running, 
        it acquires waveform data according to its current settings.'''
        self.instrument.write(":RUN")

    def iStop(self):#✅
        '''Stops the acquisition.'''
        self.instrument.write(":STOP")

    def iStartSingleAcquisition(self):#✅
        '''Clears status and starts single acquisition. <br>
    Single acquisition starts one acquisition cycle and then stops. <br>
    If segmented acquisition is enabled, it acquires the configured number of segments.
    '''
        self.instrument.write("*CLS")
        self.instrument.write(":SINGle")

        return self.iReadAcquisitionDone()
    
    def iReadAcquisitionDone(self):#✅
        '''Returns 1 if acquisition is complete, otherwise 0.'''
        response = self.instrument.query(":ADER?")
        return int(response)

    def iSaveMReport(self, filepath: str=None, extension: str="pdf"):#✅
        '''Saves MReport to a file. Possible extensions: "pdf", "mht".'''
        if filepath is None:
            print("Did not save Measurement report, as the filepath is None.")
            return
        self.instrument.write(f':DISK:SAVE:MREPort "{filepath + "." + extension.lower()}"')



    # ----------------------------------------------------------------
    # Disk commands (all start with :DISK). Used for saving options.
    # Other DISK commands: iSaveSetupToFile(), iLoadSetupFromFile(),
    # iSetSaveAllSegments().
    # ----------------------------------------------------------------
    def iMakeDirectory(self, dir_to_make: str, is_full_path: bool = False):#✅
        '''Creates a directory on the oscilloscope in the default parent directory. <br>
        Use is_full_path = True if you give a full directory (like starting with C:\\). <br>
        Otherwise the new directory will be created in C:\\Users\\Public\\Documents\\Infiniium.'''
        if not dir_to_make:
            print("Did not create a directory on the oscilloscope, as dir_to_make was not given.")
            return
        if is_full_path:
            self.instrument.write(f':DISK:MDIRectory "{dir_to_make}"')
        else:
            self.instrument.write(f':DISK:MDIRectory "{SCOPE_WAVEFORM_DIR.replace("\\Waveforms", "") + "\\" + dir_to_make.strip("\\")}"')

    def iCheckAndMakeDirectory(self, scope_directory: str):   #NOT TESTED~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        '''Checks if a directory exists on the oscilloscope. If not, creates it.'''
        scope_directory = scope_directory.rstrip(r"\\")

        parent_directory = scope_directory.rsplit(r"\\", 1)[0]
        new_directory_name = scope_directory.rsplit(r"\\", 1)[1]

        response = self.instrument.query(f':DISK:CATalog? "{parent_directory}"')

        # if directory already exists, does nothing
        if new_directory_name in response:
            print(f"Directory already exists: {scope_directory}")
            return

        # if does not exits, creates directory
        self.instrument.write(f':DISK:MDIRectory "{scope_directory}"')

    # def iRequestFileFromScope(self, scope_filepath: str):   #NOT TESTED~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     '''Requests a file from the oscilloscope disk.
    #     After this command, the file must be read as a binary block.'''

    #     self.iWrite(f':DISK:GETFILE? "{scope_filepath}"')


    
    def iRequestFileFromScope(self, scope_filepath: str):
        command = f':DISK:GETFILE? "{scope_filepath}"'

        print("Before VISA write", flush=True)

        bytes_written = self.instrument.write(command)

        print(
            f"After VISA write: {bytes_written} bytes written",
            flush=True
        )





    def iDeleteFileFromScope(self, scope_filepath: str):#✅
        '''Deletes a file from scope.'''
        try:
            self.iWrite(f':DISK:DELete "{scope_filepath}"')
        except:
            print(f"ERROR trying to delete '{scope_filepath}'.")



    # ----------------------------------------------------------------
    # Channel setup commands (all start with :CHANnel)
    # ----------------------------------------------------------------
    def iSetChannelScale(self, channel: int, v_scale: float=None):#✅
        '''Sets the vertical scale of a channel in Volts/division.'''
        if v_scale != None:
            self.instrument.write(f":CHANnel{int(channel)}:SCALe {v_scale}")

    def iReadChannelScale(self, channel: int):#✅
        '''Reads channel vertical scale in Volts/division.'''
        response = self.instrument.query(f":CHANnel{int(channel)}:SCALe?")
        return float(response)

    def iSetChannelRange(self, channel: int, v_range: float=None):#✅
        '''Sets the vertical range of a channel in Volts.'''
        if v_range != None:
            self.instrument.write(f":CHANnel{int(channel)}:RANGe {v_range}")

    def iReadChannelRange(self, channel: int):#✅
        '''Reads the vertical range of a channel in Volts.'''
        response = self.instrument.query(f":CHANnel{int(channel)}:RANGe?")
        return float(response)

    def iSetChannelOffset(self, channel: int, v_offset: float=None):#✅
        '''Sets the vertical offset of a channel in Volts.'''
        if v_offset != None:
           self.instrument.write(f":CHANnel{int(channel)}:OFFSet {v_offset}")

    def iReadChannelOffset(self, channel: int):#✅
        '''Reads channel vertical offset in Volts.'''
        response = self.instrument.query(f":CHANnel{channel}:OFFSet?")
        return float(response)

    def iSetChannelDisplay(self, channel: int, state: bool=None):#✅
        '''Turns channel display on or off. Expected input: 0/False or 1/True.'''
        if state != None:
            self.instrument.write(f":CHANnel{int(channel)}:DISPlay {int(state)}")

    def iSetChannelProbe(self, channel:int, probe: int=1):  #NOT TESTED
        '''Sets the probe.'''
        self.instrument.write(f":CHANnel{channel}:PROBe {probe}")

    def iReadChannelProbe(self, channel:int):               #NOT TESTED
        '''Checks and returns channel probe.'''
        response = self.instrument.query(f":CHANnel{channel}:PROBe?")
        return float(response.strip().split(",")[0])



    # ----------------------------------------------------------------
    # Timebase setup commands (all begin with :TIMebase)
    # ----------------------------------------------------------------
    def iSetTimebasePosition(self, time_offset_s: float):#✅❓❓❓❓❓
        '''Sets the horizontal time offset in seconds.'''
        if not time_offset_s:
            return
        self.instrument.write(f":TIMebase:POSition {time_offset_s}")

    def iReadTimebasePosition(self):#✅❓❓❓❓❓
        '''Reads the horizontal time offset in seconds.'''
        response = self.instrument.query(":TIMebase:POSition?")
        return float(response)

    def iSetTimebaseRange(self, time_range_s: float):#✅
        '''Sets the full horizontal time range in seconds.
        The range value is ten times the time-per-division value.'''
        if not time_range_s:
            return
        self.instrument.write(f":TIMebase:RANGe {time_range_s}")

    def iReadTimebaseRange(self):#✅
        '''Reads the horizontal time range in seconds.'''
        response = self.instrument.query(":TIMebase:RANGe?")
        return float(response)
    
    def iSetTimebaseReferencePercent(self, reference_percent: float = 50):#✅❓❓❓❓❓
        '''Sets the horizontal reference position in percent of the screen.'''
        if not reference_percent:
            return
        self.instrument.write(f":TIMebase:REFerence:PERCent {reference_percent}")

    def iReadTimebaseReferencePercent(self):#✅❓❓❓❓❓
        '''Reads the timebase reference in percents.'''
        response = self.instrument.query(":TIMebase:REFerence:PERCent?")
        return float(response)

    def iSetTimebaseScale(self, seconds_per_div: float):#✅
        '''Sets the time base scale in seconds per division. '''
        if not seconds_per_div:
            return
        self.instrument.write(f":TIMebase:SCALe {seconds_per_div}")

    def iReadTimebaseScale(self):#✅
        '''Returns the timebase scale (in seconds/division).'''
        response = self.instrument.query(":TIMebase:SCALe?")
        return float(response)



    # ----------------------------------------------------------------
    # Trigger setup and trigger commands (adjusted mainly for 
    # "SEQuence" triggering method).
    # ----------------------------------------------------------------
    def iSetTriggerMode(self, mode: str="SEQuence"):
        '''Sets trigger mode. <br> Default: "SEQuence". <br> Examples: "SEQuence"/"EDGE"/"GLITCH", etc.'''
        self.instrument.write(f":TRIGger:MODE {mode}")

    def iReadTriggerMode(self):
        '''Reads trigger mode. Returns "SEQ" for "SEQuence", etc.'''
        return self.instrument.query(":TRIGger:MODE?").strip()

    def iSetTriggerLevel(self, channel: int, level: float):
        '''Sets trigger level for a channel in Volts.'''
        if not channel:
            print(f"Did not set TRIGGER LEVEL as no channel was specified.")
            return
        if not level:
            print(f"Did not set TRIGGER LEVEL for {channel}, as no trigger level was provided.")
            return
        self.instrument.write(f":TRIGger:LEVel CHANnel{int(channel)},{level}")

    def iReadTriggerLevel(self, channel: int):
        '''Returns trigger level of a channel in Volts.'''
        response = self.instrument.query(f":TRIGger:LEVel? CHANnel{int(channel)}")
        return float(response)

    def iSetSequenceTriggerTerms(self, term_1: str="EDGE1", term_2: str="EDGE2"):
        '''Sets sequence trigger terms EDGE1 and EDGE2 by default. Can change term_1 and term_2 parameters if needed.'''
        self.instrument.write(f":TRIGger:SEQuence:TERM1 {term_1}")
        self.instrument.write(f":TRIGger:SEQuence:TERM2 {term_2}")

    def iSetSequenceTriggerResetTime(self, state: bool, reset_time_s: float = 1e-7):    #Tested. state works, reset time_s does not work.
        '''Sets sequence trigger reset to time mode.'''
        if state == 1:
            self.instrument.write(":TRIGger:SEQuence:RESet:ENABle 1")
            self.instrument.write(":TRIGger:SEQuence:RESet:TYPE TIME")
            self.instrument.write(f":TRIGger:SEQuence:RESet:TIME {reset_time_s}")
        else:
            self.instrument.write(":TRIGger:SEQuence:RESet:ENABle 0")

    def iSetTriggerEdge(self, edge_number: int, channel: int, slope: str):
        '''Sets edge trigger source and slope. Slope expected: "POSitive" or "NEGative".'''
        self.instrument.write(f":TRIGger:EDGE{int(edge_number)}:SOURce CHAN{int(channel)}")
        self.instrument.write(f":TRIGger:EDGE{int(edge_number)}:SLOPe {slope}")

########iSetSequenceANDState(which_AND: int, state: bool): turns on or off

    def iResetTriggerAND(self, which_AND: int):
        '''Resets the "AND" qualifiers for all channels to DONTcare, then disables the "AND"-s.'''
        if not which_AND:
            print("No SEQUENCE TRIGGER AND was reset, as none was specified.")
            return
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 1, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 2, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 3, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 4, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 5, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 6, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 7, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:CHANnel 8, DONTcare")
        self.iWrite(f":TRIGger:AND{which_AND}:ENABle 0")

    def iResetTriggerANDs(self):
        '''Resets all the "AND" qualifiers in the SEQuence triggering mode.'''
        self.iResetTriggerAND(which_AND=1)
        self.iResetTriggerAND(which_AND=2)
    
    def iSetSequenceTriggerAND(self, which_AND: int, channel: int, condition: str="DONTcare", state: int=1):
        '''Sets up the "AND" Qualifier in "sequence" triggering option - enables it, configures it. <br>
        ● condition: "HIGH"/"LOW"/"DONTcare" - this is the condition channel's 
        signal must meet with respect to the trigger level, <br>
        ● which_AND: 1 or 2, <br>
        ● channel: the channel you want to use with "AND" logic condition, <br>
        ● state: 0 or 1.
        '''
        self.instrument.write(f":TRIGger:AND{which_AND}:ENABle {state}")
        self.instrument.write(f':TRIGger:AND{which_AND}:SOURce CHANnel{channel},{condition}')



    # ----------------------------------------------------------------
    # Working with setups/setup files
    # ----------------------------------------------------------------
    def iStoreSetup(self, setup_id: int): # Not tested
        '''Stores the current setup to the setup_id setup. Expects 0-9.'''
        self.instrument.write(f":STORe:SETup {setup_id}")

    def iSaveSetupToFile(
            self, 
            directory: str=SCOPE_WAVEFORM_DIR.replace(
            r"\Waveforms",
            r"\CustomSetups"), 
            filename: str=None 
            ):
        '''Saves the current setup to a file.'''
        if filename == None:
            t = time.localtime()
            date_time_string = f"{t.tm_mday}{time.strftime('%b%Y-%H%M%S', t)}"
            filename = f"CustomSetup_{date_time_string}"
            filepath = self.iJoinScopePath(directory, filename=filename)
        else:
            filepath = self.iJoinScopePath
            self.instrument.write(f':DISK:SAVE:SETup "{filepath}"')

    def iRecallSetup(self, setup_number: int):
        '''Recalls a setup that was saved in one of the oscilloscope's setup memories.
        Expects 0-9.'''
        self.instrument.write(f":RECall:SETup {setup_number}")

    def iLoadSetupFromFile(self, setup_filepath: str):
        '''Loads a specified setup file. Need to give the whole path.'''
        self.instrument.write(f':DISK:LOAD "{setup_filepath}"')



    # ----------------------------------------------------------------
    # Miscellaneous
    # ----------------------------------------------------------------
    def iPrintScopeErrors(self, label:str=None):
        print(label)
        print("Errors: ", self.iReadErrors())

    def iSetAutoscale(self):
        '''Auto-scales the timebase and channel axes to display [PROBABLY NOT SO USEFUL].'''
        self.instrument.write(":AUToscale")

    def iReadModel(self):
        '''Returns the model of the oscilloscope.'''
        response = self.instrument.write(":MODel?")
        return response

    def iClearStatus(self):
        '''Clears the status and error registers.'''
        self.instrument.write("*CLS")

    def iReadIdentity(self):
        '''Reads the oscilloscope identifiers. You can use mostly to test communication.'''
        return self.instrument.query("*IDN?").strip()

    def iReset(self):
        '''Resets the oscilloscope to the default setup.'''
        self.instrument.write("*RST")
        time.sleep(0.5)
    
    def iReadOperationComplete(self):
        '''Reads operation complete status.'''
        return int(self.instrument.query("*OPC?"))

    def iBeep(self, freq: float, dur: float): # Tested, did NOT work
        '''Makes the oscilloscope beep with frequency 'freq' [Hz] 
        and duration 'dur' [ms].'''
        self.instrument.write(f":BEEP {freq},{dur}")

    def iClearDisplay(self):
        '''Clears the oscilloscope display. Resets all associated measurements. 
        If the oscilloscope is stopped, all currently displayed data is erased.
        Waveform memories are not erased.'''
        self.instrument.write(":CDISplay")

    def iReadErrors(self):
        '''Reads the oscilloscope error queue.'''
        return self.instrument.query(":SYSTem:ERRor?").strip()

    def iJoinScopePath(self, scope_directory: str, filename: str): # to test
        '''Joins paths (a directory and ), assuming it is a Windows directory.'''
        return scope_directory.rstrip("\\/") + "\\" + filename.strip("\\/")



    # ----------------------------------------------------------------
    # Closing the InfiniiumScope instances.
    # ----------------------------------------------------------------
    def iClose(self):
        '''Closes the oscilloscope. The same as iCloseLecroy()'''
        self.instrument.close()
        self.rm.close()

    def iCloseLecroy(self):
        '''Closes the oscilloscope. The same as iClose()'''
        self.iClose()



    # ----------------------------------------------------------------
    # These 2 definitions allow using InfiniiumScope in a "with" statement.
    # ----------------------------------------------------------------
    def __enter__(self):
        '''Allows use with with-statement.'''
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Closes the oscilloscope when leaving with-statement.'''
        self.close()



    # ----------------------------------------------------------------
    # "Higher level of abstraction" commands
    # ----------------------------------------------------------------

    def iSetupHorizontal(
            self,
            timebase_scale: float,
            timebase_offset: float,
            timebase_reference_percent: int
    ):
        '''Sets horizontal parameters. <br> 
        ● scale: [s], <br> 
        ● offset: [s], <br> 
        ● reference: [%].'''

        self.iSetTimebaseScale(timebase_scale)        
        self.iSetTimebasePosition(timebase_offset)
        self.iSetTimebaseReferencePercent(timebase_reference_percent)

        self.iReadOperationComplete()
    
    def iSetupAcquisition(
            self,
            segment_count: int,
            sample_rate: int=20e9,
            acquisition_mode: str="SEGmented",
            which_segments_to_save: str="ALL",
            interpolation: bool=False,
            sample_per_segment: any=None
    ):
        '''Sets up acquisition parameters with one command. <br>
        ● segment_count: number of events to be acquired, <br>
        ● sample_rate: in [sample/s]. 20GSa/s by default, <br>
        ● acquisition_mode: written for "SEGmented", <br>
        ● which_segments_to_save: refer to iSetWhichSegmentsToSave(), <br>
        ● interpolation: refer to iSetInterpolation(). <br>
        ● sample_per_segment: can be integer, or "MAX" (NOT RECOMMENDED, AS CAN CAUSE CRASHES), or "AUTO".
        '''
        self.iSetAcquisitionMode(acquisition_mode)
        self.iSetSegmentCount(segment_count)
        self.iSetSampleRate(sample_rate)
        self.iSetWhichSegmentsToSave(which_segments_to_save)
        self.iSetInterpolation(interpolation)

        if sample_per_segment != None:
            try:
                self.iSetSamplePerSegment(sample_per_segment=sample_per_segment)
            except:
                print("ERROR setting up sample per segment.")

        self.iReadOperationComplete()

    def iSetupVertical(
            self,
            channel_display_on: list[bool | None] = None,
            vertical_scales: list[float | None] = None,
            vertical_offsets: list[float | None] = None
        ):
        '''Sets up each channel's vertical parameters. <br>
        ● channel_display_on: True/False list of 8 elements. If True, channel will be displayed. <br>
        ● vertical_scales: Vertical scale list of 8 elements in Volts/div. <br>
        ● vertical_offsets: Vertical offset list of 8 elements in Volts. <br>
        ● Use None for the channels you do not want to change.
        '''

        if channel_display_on is None:
            channel_display_on = [None, None, None, None, None, None, None, None]
        if vertical_scales is None:
            vertical_scales = [None, None, None, None, None, None, None, None]
        if vertical_offsets is None:
            vertical_offsets = [None, None, None, None, None, None, None, None]
        if len(channel_display_on) != 8:
            raise ValueError("channel_display_on must have 8 elements.")
        if len(vertical_scales) != 8:
            raise ValueError("vertical_scales must have 8 elements.")
        if len(vertical_offsets) != 8:
            raise ValueError("vertical_offsets must have 8 elements.")
        
        for i_channel in range(8):

            channel = i_channel + 1

            if channel_display_on[i_channel] is not None:
                self.iSetChannelDisplay(
                    channel=channel,
                    state=int(channel_display_on[i_channel])
                )

            if vertical_scales[i_channel] is not None:
                self.iSetChannelScale(
                    channel=channel,
                    v_scale=vertical_scales[i_channel]
                )

            if vertical_offsets[i_channel] is not None:
                self.iSetChannelOffset(
                    channel=channel,
                    v_offset=vertical_offsets[i_channel]
                )
        self.iReadOperationComplete()

    def iSaveSingleChannelWaveform(
            self, 
            channel_number: int,
            scope_saving_directory: str = SCOPE_WAVEFORM_DIR,
            filename: str = None,
            file_format: str = "H5",
            header_state: bool = True,
            get_filepath: bool = True
        ):
        '''Saves one channel waveform to the oscilloscope disk. And gets filepath as a string output. <br>
        "H5" outputs data in Volts and Seconds.'''

        import time

        file_format = file_format.upper()
        extension = "." + file_format.lower()

        if filename is None:
            t = time.localtime()
            filename = f"Waveform_Ch{int(channel_number)}_{t.tm_mday}{time.strftime('%b%Y-%H%M%S', t)}"

        # remove extension if user accidentally gave it
        if filename.lower().endswith(extension):
            filename_without_extension = filename[:-len(extension)]
        else:
            filename_without_extension = filename

        file_path_without_extension = self.iJoinScopePath(
            scope_directory=scope_saving_directory,
            filename=filename_without_extension
        )

        file_path_with_extension = file_path_without_extension + extension

        if header_state:
            header_state_string = "ON"
        else:
            header_state_string = "OFF"

        self.iWrite(
            f':DISK:SAVE:WAVeform CHANnel{int(channel_number)},'
            f'"{file_path_without_extension}",{file_format},{header_state_string}'
        )

        if get_filepath:
            return file_path_with_extension
        else:
            return
                
    def iCopyFile(
            self,
            scope_filepath: str,
            pc_output_directory: str,
            overwrite_existing: bool = False,
            chunk_size_bytes: int = 1*1024*1024,
            get_filepath: bool = True
        ):
        """Copies one file from the oscilloscope disk to a PC directory."""

        import os
        import ntpath
        import time

        chunk_size_bytes = int(chunk_size_bytes)

        if chunk_size_bytes <= 0:
            raise ValueError(
                "chunk_size_bytes must be greater than zero."
            )

        os.makedirs(pc_output_directory, exist_ok=True)

        scope_filepath = scope_filepath.strip()
        pc_filename = ntpath.basename(
            scope_filepath.rstrip("\\/")
        )

        if pc_filename == "":
            raise ValueError(
                f"Could not get filename from: {scope_filepath}"
            )

        pc_filepath = os.path.join(
            pc_output_directory,
            pc_filename
        )

        temporary_filepath = pc_filepath + ".part"

        if os.path.exists(pc_filepath) and not overwrite_existing:
            raise FileExistsError(
                f"PC file already exists: {pc_filepath}\n"
                "Use overwrite_existing=True if you want to overwrite it."
            )

        old_chunk_size = self.instrument.chunk_size
        self.instrument.chunk_size = chunk_size_bytes

        try:
            print(f"Copying from scope: {scope_filepath}")
            print(f"Copying to PC:      {pc_filepath}")
            print(
                f"VISA chunk size:    "
                f"{chunk_size_bytes / 1e6:.3f} MB"
            )

            request_start = time.perf_counter()

            self.iRequestFileFromScope(
                scope_filepath=scope_filepath
            )

            first_byte = self.instrument.read_bytes(
                1,
                break_on_termchar=False
            )

            request_seconds = (
                time.perf_counter() - request_start
            )

            if first_byte != b"#":
                raise RuntimeError(
                    "Expected binary block header '#', "
                    f"but got {first_byte!r}."
                )

            number_of_digits_byte = self.instrument.read_bytes(
                1,
                break_on_termchar=False
            )

            if not (
                b"1" <= number_of_digits_byte <= b"9"
            ):
                raise RuntimeError(
                    "Invalid binary block header. "
                    f"Length-digit byte was "
                    f"{number_of_digits_byte!r}."
                )

            number_of_digits = int(number_of_digits_byte)

            byte_count_text = self.instrument.read_bytes(
                number_of_digits,
                break_on_termchar=False
            )

            try:
                number_of_bytes = int(
                    byte_count_text.decode("ascii")
                )
            except ValueError as error:
                raise RuntimeError(
                    "Invalid binary block byte count: "
                    f"{byte_count_text!r}"
                ) from error

            print(
                f"File size:          "
                f"{number_of_bytes / 1e6:.3f} MB"
            )
            print(
                f"Response start:     "
                f"{request_seconds:.3f} s"
            )

            transfer_start = time.perf_counter()
            bytes_left = number_of_bytes
            bytes_written = 0

            with open(temporary_filepath, "wb") as output_file:
                while bytes_left > 0:
                    number_to_read = min(
                        bytes_left,
                        chunk_size_bytes
                    )

                    data = self.instrument.read_bytes(
                        number_to_read,
                        chunk_size=number_to_read,
                        break_on_termchar=False
                    )

                    if len(data) == 0:
                        raise RuntimeError(
                            "The oscilloscope returned zero bytes "
                            "before the file transfer was complete."
                        )

                    output_file.write(data)

                    number_received = len(data)
                    bytes_written += number_received
                    bytes_left -= number_received

            transfer_seconds = (
                time.perf_counter() - transfer_start
            )

            if bytes_written != number_of_bytes:
                raise RuntimeError(
                    "Incomplete file transfer: expected "
                    f"{number_of_bytes} bytes but received "
                    f"{bytes_written} bytes."
                )

            terminator_start = time.perf_counter()

            terminator = self.instrument.read_bytes(
                1,
                break_on_termchar=False
            )

            if terminator == b"\r":
                second_terminator_byte = (
                    self.instrument.read_bytes(
                        1,
                        break_on_termchar=False
                    )
                )

                terminator += second_terminator_byte

            terminator_seconds = (
                time.perf_counter() - terminator_start
            )

            if terminator not in (b"\n", b"\r\n"):
                raise RuntimeError(
                    "Unexpected data after binary block: "
                    f"{terminator!r}"
                )

            os.replace(
                temporary_filepath,
                pc_filepath
            )

            transfer_speed = (
                number_of_bytes /
                transfer_seconds /
                1e6
            )

            print(
                f"Transferred:        "
                f"{number_of_bytes / 1e6:.3f} MB"
            )
            print(
                f"Transfer time:      "
                f"{transfer_seconds:.3f} s"
            )
            print(
                f"Transfer speed:     "
                f"{transfer_speed:.3f} MB/s"
            )
            print(
                f"Terminator time:    "
                f"{terminator_seconds:.3f} s"
            )

            error_start = time.perf_counter()
            scope_errors = self.iReadErrors()
            error_seconds = time.perf_counter() - error_start

            print(
                f"Error-query time:   "
                f"{error_seconds:.3f} s"
            )
            print("Scope errors:", scope_errors)

        except Exception:
            if os.path.exists(temporary_filepath):
                os.remove(temporary_filepath)

            raise

        finally:
            self.instrument.chunk_size = old_chunk_size

        if get_filepath:
            return pc_filepath

        return
