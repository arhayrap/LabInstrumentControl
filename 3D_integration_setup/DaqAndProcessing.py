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


def run_command(command, label):
    '''Runs one terminal command and prints its output.'''

    print(f"\n[{label}]")
    print(
        " ".join(
            shlex.quote(str(item))
            for item in command
        )
    )

    process = subprocess.Popen(
        [str(item) for item in command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    if process.stdout is not None:
        for line in process.stdout:
            print(f"[{label}] {line}", end="")

    return_code = process.wait()     
    
    if return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            command
        )


def process_h5_files(
        run_number,
        h5_filepaths,
        netscope_config,
        save_meas: bool = MyConfig.iPC.preprocessor_save_waveforms
    ):
    '''Converts one HDF5 group (to root) and then runs NetScope (to preprocessed root).'''

    h5_filepaths = [
        Path(h5_filepath)
        for h5_filepath in h5_filepaths
    ]

    run_tag = h5_filepaths[0].stem

    for channel in MyConfig.iScopeConfig.channels:
        run_tag = run_tag.replace(
            f"_Ch{channel.ch_num}",
            "",
            1
        )

    converted_directory = Path(MyConfig.iPC.conv_root_dir)
    preprocessed_directory = Path(MyConfig.iPC.preprocessed_root_dir)

    converted_directory.mkdir(parents=True, exist_ok=True)
    preprocessed_directory.mkdir(parents=True, exist_ok=True)

    converted_root_filepath = (
        converted_directory
        / f"conv_{run_tag}.root"
    )

    preprocessed_root_filepath = (
        preprocessed_directory
        / f"preprocessed_{run_tag}.root"
    )

    print(f"\n[RUN {run_number} PROCESSING STARTED]")

    run_command(
        command=[
            sys.executable,
            H5_TO_ROOT_SCRIPT,
            *h5_filepaths,
            "-o",
            converted_root_filepath
        ],
        label=f"RUN {run_number} H5 TO ROOT"
    )

    if save_meas: # for saving waveforms in the preprocessed root file
        save_meas = "true"
    elif save_meas == False:
        save_meas = "false"

    run_command(
        command=[
            NETSCOPE_ANALYZER,
            f"--input_file={converted_root_filepath}",
            f"--config={netscope_config}",
            f"--output_file={preprocessed_root_filepath}",
            # "--verbose=false",
            f"--num_channels={MyConfig.iScopeConfig.channels_save_or_not.count(True)}",               #### to add
            f"--num_samples={MyConfig.iScopeConfig.acquisition_config.sample_per_segment}",           #### to add
            "--verbose=true",
            f"--save_meas={save_meas}"
        ],
        label=f"RUN {run_number} NETSCOPE"
    )

    print(f"\n[RUN {run_number} PROCESSING COMPLETE]")
    print("Converted ROOT file:")
    print(converted_root_filepath)
    print("Preprocessed ROOT file:")
    print(preprocessed_root_filepath)


# ----------------------------------------------------------------
# Main acquisition script
# ----------------------------------------------------------------
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


    # KeysightScope
    scope = InfiniiumScope()
    # LecroyScope   = TLecroyWaverunner8204()
    scope.iClearStatus()
    scope.iClearDisplay()

    scope.iStop()

    # try:
    print("Log file:")
    print(log_filepath)
    print("Processing workers:")
    print(arguments.workers)
    print("Keysight UXR Identity:", scope.iReadIdentity())
    # scope.instrument.timeout = MyConfig.iScopeConfig.scope_timeout_ms
    # # Trigger setup.
    # if MyConfig.iScopeConfig.setup_trigger_or_not:
    run_number = 0

    # -----------------------------
    # Save HDF5 waveforms on scope
    # -----------------------------
    print("\nSaving waveform files on the scope...")

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
    finally:
        print("\nCLOSING Keysight UXR0104B Oscilloscope instance...")
        try:
            keysight_scope.iClose()
            print("Keysight UXR0104B Oscilloscope instance CLOSED")
        except Exception:
            print("ERROR closing Keysight UXR0104B Oscilloscope instance.")

        print("DAQ ran ", time.time() - initial_time, "seconds.")
        print("\nExecution complete.")
        print("Log file:")
        print(log_filepath)

        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_file.close()
    '''

if __name__ == "__main__":
    main()
