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
import asyncio

sys.path.append('../')

# Local imports
from classes.Keithley2410_class import Keithley2410
from classes.KeysightUXR_class import InfiniiumScope
from classes.TLecroyWaverunner8208 import TLecroyWaverunner8208
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
        20, 20, 20, 20, 20, 20, 500, 200
    ]
    
    VOffset = [
        0, 0, 0, 0, 0, 0, 0, 0
    ]
    
    TDiv = 5
    TDelay = 15 # 100
    trigger_channel = "EXT" # "C1"
    trigger_level = 500
    bv = 117
    n_seq = int(MyConfig.iScopeConfig.acquisition_config.segment_count)

    TLecroyWaverunnerScope = TLecroyWaverunner8208()
    path = "D:/Waveforms/C1--Trace1470.trc" 
    path = "D:/Waveforms/C1--DJ_LGAD_50um_strip_NEv15000_BV117000mV_MCP4400_3--00000.trc"
    TLecroyWaverunnerScope.instrument.write(f"TRFL? DISK,HDD,FILE, '{path}'")
    response = TLecroyWaverunnerScope.instrument.read_raw()
    print(response.find(b"#9"))
    
    # response = TLecroyWaverunnerScope.instrument.read_bytes()
    # TLecroyWaverunnerScope.iCopyFile(scope_filepath = path, pc_output_directory = "/home/daq/LabInstrumentControl/3D_integration_setup/")
    # print(response)

    TLecroyWaverunnerScope.iClose()


if __name__ == "__main__":
    main()
