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

    KeysightScope = InfiniiumScope()
    # LecroyScope = TLecroyWaverunner8204()
    
    
    KeysightScope.instrument.timeout = 60000
    
    # keithley = Keithley2410()
    # keithley.kQuery("*IDN?")
    
    channels_to_save = []
    for channel in MyConfig.iScopeConfig.channels:
        if channel.save_channel:
            channels_to_save.append(channel)

    filepaths_to_copy_from_scope = []
    '''
    for channel in channels_to_save:

        filename = (
            f"{MyConfig.iScopeConfig.acquisition_config.filename_prefix}_"
            f"Ch{channel.ch_num}_"
            f"NEv{MyConfig.iScopeConfig.acquisition_config.segment_count}_"
            f"BV{int(abs(bv)*1000)}mV_"
            f"MCP{MyConfig.iScopeConfig.mcp_bias_voltage}"
        )
        
        filename = (
            "C1_DJ_LGAD_50um_strip_Ch1_NEv200_BV117000mV_MCP4400.h5"
            # "DJ_LGAD_50um_strip_Ch1_NEv200_BV117000mV_MCP4400.h5"
        )
        
        # print(MyConfig.iScopeConfig.h5_dir, filename)

        # filepath_to_copy_from_scope = (
        #     KeysightScope.iSaveSingleChannelWaveform(
        #         channel_number=channel.ch_num,
        #         scope_saving_directory=(MyConfig.iScopeConfig.h5_dir),
        #         filename=filename,
        #         file_format=(MyConfig.iScopeConfig.acquisition_config.raw_data_extension),
        #         header_state=(MyConfig.iScopeConfig.acquisition_config.save_h5_header),
        #         get_filepath=True
        #     )
        # )

        # filepaths_to_copy_from_scope.append(filepath_to_copy_from_scope)
        filepaths_to_copy_from_scope.append(filename)

        # KeysightScope.iPrintScopeErrors(f"-----After trying to SAVE CHANNEL {channel.ch_num}---------")
        # print(KeysightScope.iQuery("SYSTem:ERRor?"))
    '''
    print("\nCopying saved files from scope to PC...")

    filepaths_copied_to_pc = []

    print("\nCopied PC files:")
    for filepath in filepaths_copied_to_pc:
        print(filepath)

    # -----------------------------
    # Copy saved files from scope to PC
    # -----------------------------
    print("\nCopying saved files from scope to PC...")
    
    filepaths_copied_to_pc = []
    filenames = (
        f"{MyConfig.iScopeConfig.h5_dir}\C1_DJ_LGAD_50um_strip_Ch1_NEv200_BV117000mV_MCP4400.h5",
        # f"{MyConfig.iScopeConfig.h5_dir}\DJ_LGAD_50um_strip_Ch1_NEv200_BV117000mV_MCP4400.h5"
    )
    # for filepath_to_copy_from_scope in filepaths_to_copy_from_scope:
    for filepath_to_copy_from_scope in filenames:
        filepath_copied_to_pc = (
            KeysightScope.iCopyFile(
                scope_filepath=filepath_to_copy_from_scope,
                pc_output_directory=MyConfig.iPC.h5_dir,
                overwrite_existing=overwriteRawDataFilesOnPC,
                # chunk_size_bytes=10000000,
                get_filepath=True
            )
        )

        print(KeysightScope.iQuery("SYSTem:ERRor?"))

        filepaths_copied_to_pc.append(filepath_copied_to_pc)

        print("\nCopied PC files:")

    for filepath in filepaths_copied_to_pc:
        print(filepath)
    
    KeysightScope.iClose()


if __name__ == "__main__":
    main()
