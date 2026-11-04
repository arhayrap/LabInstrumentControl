#!/usr/bin/env python3
'''
# Example usage
python relative/path/to/file --workers 4 

Samvel Aghavelyan, 09Jul2025
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

# Local imports
from classes.Keithley2410_class import Keithley2410
from classes.KeysightUXR_class import InfiniiumScope
from workspace_3x3_Board16ch import Configs_3x3 as MyConfig


H5_TO_ROOT_SCRIPT = MyConfig.iPC.h5_to_root_converter_path
NETSCOPE_ANALYZER = MyConfig.iPC.preprocessor
autoDeleteRDFromScope = MyConfig.iScopeConfig.auto_delete_h5
overwriteRawDataFilesOnPC = MyConfig.iPC.overwrite_h5_files_on_pc


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

        parser.add_argument(
            "--yaml_config",
            type=Path,
            default=None,
            help="Path to the yaml config file.",
            required=False
        )

        arguments = parser.parse_args()
    except:
        print("ERROR while parsing arguments.")

    # Setting up the log file
    try:
        log_filepath = MyConfig.iPC.log_directory + f"/log_{datetime.now().strftime('%Y%b%d_%Hh%Mm')}.txt"

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        log_file = open(log_filepath, "w", buffering=1)

        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
    except:
        print("ERROR while setting up the log file.")


    processing_pool = ThreadPoolExecutor(max_workers=arguments.workers)
    processing_jobs = []


    scope = InfiniiumScope()

    scope.iClearStatus()
    scope.iClearDisplay()

    if MyConfig.iScopeConfig.reset_scope_upon_initialization:
        scope.iReset()

    scope.iStop()


    # try:
    keithley = Keithley2410()

    keithley.kClearStatus()
    keithley.kConfigureVoltageSource()
    # keithley.kRamp(v_final=0, v_per_s=10, v_step=0.5)
    # keithley.kRampDown(v_per_s=10)
    # keithley.kOutputOff()
    keithley.kOutputOn()
    keithley.kSetMeasureFunctionCurrent()
    keithley.kSetVoltageSourceRange(1000)
    # except:
    #     print("ERROR while connecting to Keithley 2410 power supply.")


    try:

        print("Log file:")
        print(log_filepath)

        print("Processing workers:")
        print(arguments.workers)

        print("Keysight UXR Identity:", scope.iReadIdentity())
        # scope.instrument.timeout = MyConfig.iScopeConfig.scope_timeout_ms

        # # Trigger setup.
        if MyConfig.iScopeConfig.setup_trigger_or_not:
            try:
                scope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch1.ch_num,
                    level=MyConfig.iScopeConfig.ch1.trigger_level
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 1====")

                scope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch2.ch_num,
                    level=MyConfig.iScopeConfig.ch2.trigger_level
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 2====")


                scope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch3.ch_num,
                    level=MyConfig.iScopeConfig.ch3.trigger_level
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 3====")

                scope.iSetTriggerLevel(
                    channel=MyConfig.iScopeConfig.ch4.ch_num,
                    level=MyConfig.iScopeConfig.ch4.trigger_level
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER LEVEL CH 4====")




                scope.iSetTriggerMode(
                    MyConfig.iScopeConfig.trigger_config.mode
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER MODE SETUP====")


                scope.iSetSequenceTriggerTerms(
                    term_1=MyConfig.iScopeConfig.trigger_config.sequence_term_1,
                    term_2=MyConfig.iScopeConfig.trigger_config.sequence_term_2
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER TERM SETUP====")


                scope.iSetTriggerEdge(
                    edge_number=1,
                    channel=MyConfig.iScopeConfig.trigger_config.sequence_term_1_ch,
                    slope=MyConfig.iScopeConfig.trigger_config.edge_1_polarity
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER EDGE 1 SETUP====")


                scope.iSetTriggerEdge(
                    edge_number=2,
                    channel=MyConfig.iScopeConfig.trigger_config.sequence_term_2_ch,
                    slope=MyConfig.iScopeConfig.trigger_config.edge_2_polarity
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER EDGE 2 SETUP====")


                scope.iSetSequenceTriggerAND(
                    which_AND=2, 
                    channel=MyConfig.iScopeConfig.ch2.ch_num, 
                    condition="HIGH",
                    state=1
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER AND  SETUP====")



                scope.iSetSequenceTriggerResetTime(
                    state=MyConfig.iScopeConfig.trigger_config.sequence_reset,
                    reset_time_s=MyConfig.iScopeConfig.trigger_config.sequence_reset_time
                )
                scope.iPrintScopeErrors("====AFTER TRIGGER RESET TIME SETUP====")


            except:
                print("ERROR while setting up the trigger.")
            finally:
                scope.iPrintScopeErrors("-----After TRIGGER setup-------------------")
        else:
            print("Skipping trigger setup.")

        # Horizontal (timebase) setup.
        try:
            scope.iSetupHorizontal(
                timebase_scale=MyConfig.iScopeConfig.timebase_config.h_scale,
                timebase_offset=MyConfig.iScopeConfig.timebase_config.position,
                timebase_reference_percent=MyConfig.iScopeConfig.timebase_config.h_reference_percent
            )
        except:
            print("ERROR while setting horizontal/timebase scales/parameters.")
        finally:
            scope.iPrintScopeErrors("-----After HORIZONTAL setup----------------")



        # Vertical (channels )setup. 
        if MyConfig.iScopeConfig.setup_vertical_or_not:
            try:
                scope.iSetupVertical(
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
                scope.iPrintScopeErrors("-----After VERTICAL setup-------------------")


        # Acquisition parameters setup
        try:
            scope.iSetupAcquisition(
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
            scope.iPrintScopeErrors("-----After ACQUISITION setup----------------")

        # Main DAQ loop.
        for run_number, bv in enumerate(
            MyConfig.KeithleyConfig.bias_voltages,
            start=1
        ):

            keithley.kRamp(v_final=bv, v_per_s=2, v_step=0.5)
            keithley.kWrite(":DISP:ENAB ON")
            keithley.kWrite(":SYST:LOC")

            print(f"RUN: {run_number}. BIAS VOLTAGE: {bv} Volts")

            print("\n\n")
            print(f"-----After Ramping to {bv}Volts------------")
            print(f"Intended bias voltage: {keithley.kReadSetVoltage()}V."
                  f"\nActual voltage: {keithley.kMeasureVoltage()}.")

            # -----------------------------
            # Start single segmented acquisition
            # -----------------------------
            print("-----Starting single segmented acquisition--")

            scope.iStartSingleAcquisition()

            wait_for_acquisition_done(scope=scope, poll_time_s=10.0)

            scope.iPrintScopeErrors("-----After SINGLE ACQUISITION---------------")

            # -----------------------------
            # Stop before saving
            # -----------------------------
            scope.iStop()
            scope.iPrintScopeErrors("-----After STOP ----------------------------")


            # -----------------------------
            # Save HDF5 waveforms on scope
            # -----------------------------
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
                    scope.iSaveSingleChannelWaveform(
                        channel_number=channel.ch_num,
                        scope_saving_directory=(MyConfig.iScopeConfig.h5_dir),
                        filename=filename,
                        file_format=(MyConfig.iScopeConfig.acquisition_config.raw_data_extension),
                        header_state=(MyConfig.iScopeConfig.acquisition_config.save_h5_header),
                        get_filepath=True
                    )
                )

                filepaths_to_copy_from_scope.append(filepath_to_copy_from_scope)

                scope.iPrintScopeErrors(f"-----After trying to SAVE CHANNEL {channel.ch_num}---------")

            print("\nSaved scope files:")

            for filepath in filepaths_to_copy_from_scope:
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
                        chunk_size_bytes=10_000_000,
                        get_filepath=True
                    )
                )
                filepaths_copied_to_pc.append(filepath_copied_to_pc)

            print("\nCopied PC files:")

            for filepath in filepaths_copied_to_pc:
                print(filepath)

            processing_job = processing_pool.submit(
                process_h5_files,
                run_number,
                filepaths_copied_to_pc,
                MyConfig.iPC.preprocessor_config
            )

            processing_jobs.append(processing_job)

            print(f"RUN {run_number} with BIAS VOLTAGE {bv} V is complete.")

            print(f"RUN {run_number} processing started in the background.")

            if autoDeleteRDFromScope:
                for filepath in filepaths_to_copy_from_scope:
                    scope.iDeleteFileFromScope(filepath)


        print("ALL DAQs COMPLETE.")

    except KeyboardInterrupt:
        print("\nExecution stopped by Ctrl+C.")

    finally:

        print("\nCLOSING Keysight UXR0104B Oscilloscope instance...")
        try:
            scope.iClose()
            print("Keysight UXR0104B Oscilloscope instance CLOSED")
        except Exception:
            print("ERROR closing Keysight UXR0104B Oscilloscope instance.")


        print("\nCLOSING Keithley 2410 Power Supply instance...")
        try:
            keithley.kSafeShutdown(v_per_s=5)
            keithley.kClose()
            print("Keithley 2410 Power Supply instance CLOSED")
        except Exception:
            print("ERROR closing Keithley 2410 Power Supply instance.")

        print("\nWaiting for processing jobs...")

        processing_pool.shutdown(wait=True)

        for processing_job in processing_jobs:
            try:
                processing_job.result()
            except Exception as error:
                print("\nPROCESSING JOB FAILED (AT LEAST) AFTER TRYING TO SHUT DOWN. SEE ERROR BELOW:")
                print(error)
                print("YOU MAY WANT TO CHECK THE INTERNAL STRUCTURE OF A PREPROCESSED FILE.")

        print("DAQ ran ", time.time() - initial_time, "seconds.")
        print("\nExecution complete.")
        print("Log file:")
        print(log_filepath)

        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_file.close()


if __name__ == "__main__":
    main()
