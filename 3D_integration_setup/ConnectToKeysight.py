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
    LecroyScope = TLecroyWaverunner8204()
    
    # keithley = Keithley2410()
    # keithley.kQuery("*IDN?")
    
    try:

        if MyConfig.iScopeConfig.setup_trigger_or_not:
            try:
                KeysightScope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch1.ch_num,
                    level=MyConfig.iScopeConfig.ch1.trigger_level
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 1====")

                KeysightScope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch2.ch_num,
                    level=MyConfig.iScopeConfig.ch2.trigger_level
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 2====")

                KeysightScope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch3.ch_num,
                    level=MyConfig.iScopeConfig.ch3.trigger_level
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 3====")

                KeysightScope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch4.ch_num,
                    level=MyConfig.iScopeConfig.ch4.trigger_level
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 4====")
                
                
                
                KeysightScope.iSetTriggerMode(
                    MyConfig.iScopeConfig.trigger_config.mode
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER MODE SETUP====")


                KeysightScope.iSetSequenceTriggerTerms(
                    term_1=MyConfig.iScopeConfig.trigger_config.sequence_term_1,
                    term_2=MyConfig.iScopeConfig.trigger_config.sequence_term_2
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER TERM SETUP====")


                KeysightScope.iSetTriggerEdge(
                    edge_number=1,
                    channel=MyConfig.iScopeConfig.trigger_config.sequence_term_1_ch,
                    slope=MyConfig.iScopeConfig.trigger_config.edge_1_polarity
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER EDGE 1 SETUP====")


                KeysightScope.iSetTriggerEdge(
                    edge_number=2,
                    channel=MyConfig.iScopeConfig.trigger_config.sequence_term_2_ch,
                    slope=MyConfig.iScopeConfig.trigger_config.edge_2_polarity
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER EDGE 2 SETUP====")


                KeysightScope.iSetSequenceTriggerAND(
                    which_AND=2, 
                    channel=MyConfig.iScopeConfig.ch2.ch_num, 
                    condition="HIGH",
                    state=1
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER AND  SETUP====")

                KeysightScope.iSetSequenceTriggerResetTime(
                    state=MyConfig.iScopeConfig.trigger_config.sequence_reset,
                    reset_time_s=MyConfig.iScopeConfig.trigger_config.sequence_reset_time
                )
                KeysightScope.iPrintScopeErrors("====AFTER TRIGGER RESET TIME SETUP====")
            except:
                print("ERROR while setting up the trigger.")
            finally:
                KeysightScope.iPrintScopeErrors("-----After TRIGGER setup-------------------")
        else:
            print("Skipping trigger setup.")

        # Horizontal (timebase) setup.
        try:
            KeysightScope.iSetupHorizontal(
                # timebase_scale=0.25e-9, # MyConfig.iScopeConfig.timebase_config.h_scale,
                timebase_offset=0, # MyConfig.iScopeConfig.timebase_config.position,
                timebase_reference_percent=MyConfig.iScopeConfig.timebase_config.h_reference_percent
            )
        except:
            print("ERROR while setting horizontal/timebase scales/parameters.")
        finally:
            KeysightScope.iPrintScopeErrors("-----After HORIZONTAL setup----------------")

        # Vertical (channels )setup. 
        if MyConfig.iScopeConfig.setup_vertical_or_not:
            try:
                KeysightScope.iSetupVertical(
                    channel_display_on=(
                        MyConfig.iScopeConfig.channels_display_states
                    ),
                    vertical_scales=(
                        MyConfig.iScopeConfig.channels_v_scales
                    ),
                    vertical_offsets=(
                        MyConfig.iScopeConfig.channels_v_offsets
                    )
                )
            except:
                print("ERROR while setting vertical/channel scales/parameters.")
            finally:
                KeysightScope.iPrintScopeErrors("-----After VERTICAL setup-------------------")
        
        # KeysightScope.iSetTimebaseRange(0.5e-9)
        # KeysightScope.iWrite(":TIMebase:RANGe 1e-9")
        
        # Acquisition parameters setup
        try:
            KeysightScope.iSetupAcquisition(
                segment_count=MyConfig.iScopeConfig.acquisition_config.segment_count,
                sample_rate=MyConfig.iScopeConfig.acquisition_config.sample_rate,
                acquisition_mode=MyConfig.iScopeConfig.acquisition_config.mode,
                which_segments_to_save=(
                    MyConfig.iScopeConfig.acquisition_config.save_which_segments
                ),
                interpolation=MyConfig.iScopeConfig.acquisition_config.interpolation,
                sample_per_segment=(
                    MyConfig.iScopeConfig.acquisition_config.sample_per_segment
                )
            )
        except:
            print("ERROR while setting up acquisition parameters (segment count, sample rate, etc).")
        finally:
            KeysightScope.iPrintScopeErrors()

        KeysightScope.iStartSingleAcquisition()
        wait_for_acquisition_done(scope=KeysightScope, poll_time_s=10.0)

        KeysightScope.iPrintScopeErrors("-----After SINGLE ACQUISITION---------------")
        KeysightScope.iStop()
        KeysightScope.iPrintScopeErrors("-----After STOP ----------------------------")

        print("\nSaving waveform files on the scope...")


        channels_to_save = []
        for channel in MyConfig.iScopeConfig.channels:
            if channel.save_channel:
                channels_to_save.append(channel)

        filepaths_to_copy_from_scope = []
        for channel in channels_to_save:

            filename = (
                f"{MyConfig.iScopeConfig.acquisition_config.filename_prefix}_"
                f"Ch{channel.ch_num}_"
                f"NEv{MyConfig.iScopeConfig.acquisition_config.segment_count}_"
                f"BV{int(abs(bv)*1000)}mV_"
                f"MCP{MyConfig.iScopeConfig.mcp_bias_voltage}"
            )

            filepath_to_copy_from_scope = (
                KeysightScope.iSaveSingleChannelWaveform(
                    channel_number=channel.ch_num,
                    scope_saving_directory=(MyConfig.iScopeConfig.h5_dir),
                    filename=filename,
                    file_format=(MyConfig.iScopeConfig.acquisition_config.raw_data_extension),
                    header_state=(MyConfig.iScopeConfig.acquisition_config.save_h5_header),
                    get_filepath=True
                )
            )


    for filepath in filepaths_copied_to_pc:
        print(filepath)
            filepaths_to_copy_from_scope.append(filepath_to_copy_from_scope)

            KeysightScope.iPrintScopeErrors(f"-----After trying to SAVE CHANNEL {channel.ch_num}---------")

        print("\nSaved scope files:")

        for filepath in filepaths_to_copy_from_scope:
            print(filepath)

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

    KeysightScope.iClose()


if __name__ == "__main__":
    main()
