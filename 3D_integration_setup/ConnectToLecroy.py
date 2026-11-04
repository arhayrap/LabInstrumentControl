#!/usr/bin/env python3
'''
# Example usage
python *path/to/your/autoDAQ/script* --workers 4 

Aram Hayrapetyan, 26 Oct 2026
'''

import argparse
import shlex
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.append('../')

# Local imports
from classes.Keithley2410_class import Keithley2410
from classes.KeysightUXR_class import InfiniiumScope
from classes.TLecroyWaverunner8204 import TLecroyWaverunner8204
import Configs as MyConfig

H5_TO_ROOT_SCRIPT = MyConfig.iPC.h5_to_root_converter_path
NETSCOPE_ANALYZER = MyConfig.iPC.preprocessor
autoDeleteRDFromScope = MyConfig.iScopeConfig.auto_delete_h5
overwriteRawDataFilesOnPC = True # MyConfig.iPC.overwrite_h5_files_on_pc

class Tee:
    '''Prints to both terminal and log file.'''

    def __init__(self, terminal, log_file):
        self.terminal = terminal
        self.log_file = log_file
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.terminal.write(text)
            self.terminal.flush()
            self.log_file.write(text)
            self.log_file.flush()

    def flush(self):
        with self.lock:
            self.terminal.flush()
            self.log_file.flush()


def wait_for_acquisition_done(
        scope,
        # timeout_s: float = MyConfig.iScopeConfig.scope_timeout_ms,
        poll_time_s: float = 1.0
    ):
    '''Waits until segmented single acquisition is complete.'''

    start_time = time.monotonic()

    while True:

        acquisition_done = bool(scope.iReadAcquisitionDone())

        elapsed_time = time.monotonic() - start_time

        if acquisition_done:
            print(
                f"\r\033[KAcquisition done. "
                f"Total waiting time: {elapsed_time:.1f} s"
            )
            return True

        # if elapsed_time > timeout_s:
        #     print()
        #     raise TimeoutError(
        #         f"Acquisition did not finish within {timeout_s} seconds."
        #     )

        print(
            f"\r\033[KAcquisition not done yet. "
            f"Waiting... {elapsed_time:.1f} s",
            end="",
            flush=True
        )

        time.sleep(poll_time_s)


def main():
    initial_time = time.time()

    # Parsing arguments
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--workers",
            type=int,
            default=2,
            help="Number of processing jobs to run in parallel."
        )

        arguments = parser.parse_args()
    except:
        print("ERROR while parsing arguments.")

    # Setting up the log file
    try:
        log_filepath = MyConfig.iPC.log_directory + f"/log_{datetime.now().strftime('%Y%b%d_%Hh%Mm')}.txt"
        print(log_filepath)

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        log_file = open(log_filepath, "w", buffering=1)

        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
    except:
        print("ERROR while setting up the log file.")


    processing_pool = ThreadPoolExecutor(max_workers=arguments.workers)
    processing_jobs = []
    
    VDivs = [
        20, 20, 20, 20, 20, 20, 20, 200
    ]
    
    VOffset = [
        0, 0, 0, 0, 0, 0, 0, 0
    ]
    
    TDiv = 500
    TDelay = 0 # 100
    
    trigger_channel = "C1"
    trigger_level = 10
    
    n_seq = 1000

    # scope = InfiniiumScope()
    scope = TLecroyWaverunner8204()

    try:
        print(scope.iQuery("*IDN?"))
        print(scope.iQuery("ALL_STATUS?"))
        # print(scope.iQuery("*TST?"))
        
        '''
        # set the basic display
        scope.iWrite("GRID octal")
        
        # Setup the channels ranges
        for i in range(1,9):
            scope.iWrite(f"C{i}:TRACE OFF")
            scope.iWrite(f"C{i}:TRACE ON")
            scope.iWrite(f"C{i}:VDIV {VDivs[i-1]} mV")
            scope.iWrite(f"C{i}:OFFSET {VOffset[i-1]} mV")
        '''
        
        scope.iWrite(f"TDIV {TDiv} ns")
        scope.iWrite(f"TRIG_DELAY {TDelay} ns")
        
        # scope.iWrite(f"C{i}:TOFFSET {TOffset} ns")
        # scope.iWrite("")
        
        # print(scope.iQuery("BandWidth_Limit?"))
        
        # Set the trigger and the trigger level
        
        scope.iWrite("TRIG_MODE NORMAL")
        scope.iWrite(f"{trigger_channel}:TRIG_SLOPE POS")
        scope.iWrite(f"TRIG_SELECT EDGE, SR, {trigger_channel}")
        scope.iWrite(f"TRIG_LEVEL {trigger_level} mV")
        # scope.iWrite(":ACQuire:INTerpolation LINear")

        print(scope.iQuery("?TRIG_SELECT"))
        print(scope.iQuery("?TRIG_SLOPE"))
        
        # print(scope.iQuery("SEQ:COUN?"))
        
        # scope.iWrite(f"SEQ ON, {n_seq}")
        
        # scope.iStartSingleAcquisition()
        # scope.iWrite("STOP")
        
        scope.iClose()

        # for i in [1, 2, 3]:
        #     base_path = "C:/Users/Public/Documents/Infiniium/Waveforms"
        #     base_path = "D:/Waveforms"
        #     filename = f"C{i}_DJ100W50B9_bv117_mcp4400_trigExtCh2_MCP_channel_only_10mV_HighSensHighBandwidth_zoomedin_10p5mV_30000"
        #     file_format = "h5"
        #     file_format = "trc"
        #     print(scope.iSaveSingleChannelWaveform(channel_number = i, filename = filename)) # , file_format = "trc"))
        #     scope.iCopyFile(scope_filepath = f"{base_path}/{filename}.{file_format}", pc_output_directory = "./", overwrite_existing = True)
        
        # scope.iClose()
        # scope.iClearStatus()
    
        # print(scope.iQuery("DOT_JOIN?"))
        # print(scope.iQuery("GRID_DISPLAY?"))
    
        # scope.iClearDisplay()

        # scope.iStop()
    except  KeyboardInterrupt:
        scope.iClose()
        print("\nSomething went wrong while copying")
        print("\nExecution stopped by Ctrl+C.")

    '''
    try:

    print("Log file:")
    print(log_filepath)
    print("Processing workers:")
    print(arguments.workers)
    print("Keysight UXR Identity:", scope.iReadIdentity())
    # scope.instrument.timeout = MyConfig.iScopeConfig.scope_timeout_ms
    # # Trigger setup.
    # if MyConfig.iScopeConfig.setup_trigger_or_not:
    run_number = 0

    channels_to_save = []
    for channel in MyConfig.iScopeConfig.channels:
        if channel.save_channel:
            channels_to_save.append(channel)

    filepaths_to_copy_from_scope = []
        
    for ic, channel in enumerate(channels_to_save):
        filepath_to_copy_from_scope = f"C{ic+1}_DJ100W50B9_bv120_mcp4400_trigExt_MCP_channel_only_3000_15mV.h5"
        filepaths_to_copy_from_scope.append(filepath_to_copy_from_scope)
        
    print(filepaths_to_copy_from_scope)
    
    # -----------------------------
    # Copy saved files from scope to PC
    # -----------------------------
    print("\nCopying saved files from scope to PC...")

    filepaths_copied_to_pc = []
    for filepath_to_copy_from_scope in (filepaths_to_copy_from_scope):
        filepath_copied_to_pc = (
            scope.iCopyFile(
                scope_filepath=filepath_to_copy_from_scope,
                pc_output_directory=MyConfig.iPC.h5_dir,
                overwrite_existing=overwriteRawDataFilesOnPC,
                # chunk_size_bytes=10000000,
                get_filepath=True
            )
        )
        filepaths_copied_to_pc.append(filepath_copied_to_pc)

        print("\nCopied PC files:")

    for filepath in filepaths_copied_to_pc:
        print(filepath)

    print("Before submitting the processes")
    processing_job = processing_pool.submit(
        process_h5_files,
        run_number,
        filepaths_copied_to_pc,
        MyConfig.iPC.preprocessor_config
    )
    print("After submitting the processes")

    processing_jobs.append(processing_job)

    # print(f"RUN {run_number} with BIAS VOLTAGE {bv} V is complete.")
    print(f"RUN {run_number} processing started in the background.")

    if autoDeleteRDFromScope:
        for filepath in filepaths_to_copy_from_scope:
            scope.iDeleteFileFromScope(filepath)
    
    print("ALL DAQs COMPLETE.")

    # except: #  KeyboardInterrupt:
    #     print("\nSomething went wrong while copying")
        # print("\nExecution stopped by Ctrl+C.")
    '''

if __name__ == "__main__":
    main()
