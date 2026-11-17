from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass(frozen=True)
class iChannelConfig:
    '''Below are explanations of ChannelConfig attributes: <br>
    • ch_num:                   Channel number on the scope. Accepts integers from 1-4. <br>
    • label:                    Custom name/label you want to give to the channel. Accepts string or integer. Equals to ch_num by default. <br>
    • display:                  Whether to display the channel on screen. Accepts bool: True or False. <br>
    • v_scale:                  Volts per division. There are overall 8 vertical divisions. So, equals to v_range/8. <br>
    • v_range:                  Range of y axis in [Volts]. <br>
    • v_offset:                 y offset in [Volts]. <br>
    • polarity:                 Expected channel polarity. Accepts strings "POSitive" or "NEGative". <br>
    • trigger_level:            Trigger level in [Volts]. <br>
    • probe:                    Probe attenuation factor. Equals to 1 by default. <br>
    • bias_voltage:             Bias voltage given to the device connected to the channel. <br>
    • save_channel:             Whether to save the channel waveforms or not, e.g. if Channel 1 is not used, set False. <br>
    '''
    ch_num: int
    label: str | int | None = None

    display: bool | None = False

    v_scale: float | None = None
    v_range: float | None = None
    v_offset: float | None = None

    polarity: str | None = None

    trigger_level: float | None = None

    probe: float = 1

    bias_voltage: float | None = None

    save_channel: bool = False

    def __post_init__(self):
        if self.label is None:
            object.__setattr__(self, "label", self.ch_num)


@dataclass(frozen=True)
class iAcquisitionConfig:
    '''Below are explanations of iAcquisition attributes: <br>
    • filename_prefix:          String to be added to the beginning of the files, e.g. LGAD or board name. <br>
    • mode:                     Scope acquisition mode. <br>
    • save_which_segments:      Which acquired segments to save. <br>
    • sample_rate:              Sampling rate in [Samples/second]. <br>
    • sample_per_segment:       Number of samples in every segment. <br>
    • segment_count:            Number of segments to be acquired. <br>
    • interpolation:            Scope interpolation setting. <br>
    • raw_data_extension:       File extension used when saving raw waveform data. <br>
    • save_h5_header:           Whether to save the HDF5 waveform header. Accepts bool: True or False. <br>
    '''

    filename_prefix: str | None = None

    mode: str = "SEGmented"
    save_which_segments: str = "ALL"
    sample_rate: int = 128e9
    sample_per_segment: int = 5120
    segment_count: int = None
    interpolation: int = 0

    raw_data_extension: str = "H5"
    save_h5_header: bool = True         # do not change this. Needed for h5 to root conversion.


@dataclass(frozen=True)
class iTimebaseConfig:
    '''Below are explanations of iTimebaseConfig attributes: <br>
    • position:                 Horizontal timebase position in [seconds]. <br>
    • h_range:                  Total horizontal time range in [seconds]. <br>
    • h_scale:                  Horizontal time per division in [seconds/division]. <br>
    • h_reference_percent:      Horizontal reference position in percent. Accepts values from 0-100. <br>
    '''
    position: float | None = None
    h_range: float | None = None
    h_scale: float | None = None

    h_reference_percent: int | None = None


@dataclass(frozen=True)
class iTrigger:
    '''Below are explanations of iTrigger attributes: <br>
    • setup_trigger_or_not:          Whether to setup the trigger with the script. Accepts bool: True or False. <br>
    • mode:                             Trigger mode. <br>
    • sequence_reset:                   Whether to reset the sequence trigger after the reset time. Accepts bool: True or False. <br>
    • sequence_reset_time:              Sequence trigger reset time in [seconds]. <br>
    • sequence_term_1:                  First sequence trigger term. <br>
    • sequence_term_2:                  Second sequence trigger term. <br>
    • edge_1_ch:                        Scope channel used for EDGE1. <br>
    • edge_2_ch:                        Scope channel used for EDGE2. <br>
    • edge_1_polarity:                  EDGE1 trigger polarity. Accepts strings "POSitive" or "NEGative". <br>
    • edge_2_polarity:                  EDGE2 trigger polarity. Accepts strings "POSitive" or "NEGative". <br>
    • sequence_term_1_AND_state:        Whether the first sequence trigger AND condition is enabled. Accepts bool: True or False. <br>
    • sequence_term_2_AND_state:        Whether the second sequence trigger AND condition is enabled. Accepts bool: True or False. <br>
    '''
    

    mode: str = "SEQuence"
    sequence_reset: bool | None = None
    sequence_reset_time: float | None = None
    sequence_term_1: str = "EDGE1"
    sequence_term_2: str = "EDGE2"
    sequence_term_1_ch: int | None = None
    sequence_term_2_ch: int | None = None
    edge_1_polarity: str | None = None
    edge_2_polarity: str | None = None
    


class iScopeConfig:
    '''Below are explanations of iScopeConfig attributes: <br>
    • visa_address:                    VISA address of the oscilloscope. <br>
    • visa_library_path:               Path to the VISA library. <br>
    • scope_timeout_ms:                Oscilloscope timeout in [milliseconds]. <br>
    • encoding:                        Encoding used while communicating with the oscilloscope. <br>
    • parent_dir:                      Parent directory on the oscilloscope. <br>
    • h5_dir:                          Directory on the oscilloscope where HDF5 waveform files are saved. <br>
    • setups_dir:                      Directory on the oscilloscope where setup files are saved. <br>
    • mreports_dir:                    Directory on the oscilloscope where measurement reports are saved. <br>
    • auto_delete_h5:                  Whether to delete copied HDF5 waveform files from the oscilloscope. Accepts bool: True or False. <br>
    • scope_save_mreport:              Whether to save a measurement report on the oscilloscope. Accepts bool: True or False. <br>
    '''
    # Scope initializing things
    reset_scope_upon_initialization: bool = False


    # Some global attributes
    visa_address: str = "USB0::10893::36867::MY64060141::0::INSTR"
    visa_library_path: str = "" # /opt/keysight/iolibs/libktvisa32.so"

    scope_timeout_ms: int = 600_000*100000
    encoding: str = "latin_1"

    # Scope directories
    parent_dir: str = r"C:\Users\Public\Documents\Infiniium"
    h5_dir: str = parent_dir + r"\Waveforms"
    setups_dir: str = parent_dir + r"\Setups"
    mreports_dir: str = parent_dir + r"\MReports"


    # What do you need to set up:
    setup_trigger_or_not: bool = False            # if False, iTrigger attributes below will not be set.
    setup_vertical_or_not: bool = False

    # Additional
    auto_delete_h5: bool = False
    scope_save_mreport: bool = True
    mcp_bias_voltage = 4400

    # Configuring channels
    ch1 = iChannelConfig(
        ch_num=1,
        label="Ch1",
        display=True,
        v_offset=0,
        v_scale=10,
        save_channel=True,
        trigger_level=0,
        polarity="NEGative"
    )

    ch2 = iChannelConfig(
        ch_num=2,
        label="Ch2",
        display=True,
        v_offset=0,
        v_scale=10,
        save_channel=True,
        trigger_level=-10.0,
        polarity="NEGative"
    )

    ch3 = iChannelConfig(
        ch_num=3,
        label="Ch3",
        display=True,
        v_offset=0,
        v_scale=10,
        save_channel=True,
        trigger_level=0,
        polarity="NEGative"
    )

    ch4 = iChannelConfig(
        ch_num=4,
        label="Ch4",
        display=True,
        v_offset=0,
        v_scale=10,
        save_channel=True,
        trigger_level=0,
        polarity="NEGative"
    )

    acquisition_config = iAcquisitionConfig(
        filename_prefix="AC_LGAD_40um_strip", # "T3x3_AC100_Aug4_chargeSharing_p5p6",
        segment_count=200
        # segment_count=10
    )

    timebase_config = iTimebaseConfig(
        position=0,
        h_scale=1e-9,# 2e-9,
        h_reference_percent=50
    )

    trigger_config = iTrigger(
        mode="SEQuence",
        sequence_reset=True,
        sequence_reset_time=25e-9,
        sequence_term_1="EDGE1",
        # sequence_term_2="EDGE2",
        sequence_term_1_ch=ch2.ch_num,
        # sequence_term_2_ch=ch4.ch_num,
        edge_1_polarity=ch2.polarity,
        # edge_2_polarity=ch4.polarity,
    )

    channels = [ch1, ch2, ch3, ch4]
    channels_display_states = [ch1.display, ch2.display, ch3.display, ch4.display]
    channels_v_scales = [ch1.v_scale, ch2.v_scale, ch3.v_scale, ch4.v_scale]
    channels_v_offsets = [ch1.v_offset, ch2.v_offset, ch3.v_offset, ch4.v_offset]
    channels_save_or_not = [ch1.save_channel, ch2.save_channel, ch3.save_channel, ch4.save_channel]


class iPC:
    '''Notice that all paths are relative to the current working directory which should be AutoDAQ_Final. <br>
    • h5_dir:                          Directory on the PC where copied HDF5 waveform files are saved. <br>
    • conv_root_dir:                   Directory on the PC where converted ROOT files are saved. <br>
    • preprocessed_root_dir:           Directory on the PC where preprocessed ROOT files are saved. <br>
    • h5_to_root_converter_path:       Path to the HDF5 to ROOT converter script. <br>
    • preprocessor:                    Path to the NetScopeStandalone preprocessor executable. <br>
    • preprocessor_config:             Path to the NetScopeStandalone configuration file. <br>
    • preprocessor_save_waveforms:     Whether to save waveforms in the preprocessed ROOT files. Accepts bool: True or False. <br>
    '''

    # Directories
    h5_dir: str = "../0_RawData_h5"
    conv_root_dir: str = "../1_ConvertedRoots"
    preprocessed_root_dir: str = "../2_PreprocessedRoots"
    log_directory: str = "_logs"

    # Filepaths
    h5_to_root_converter_path: str = "reconstructionTools/convertH5ToROOT.py"
    preprocessor: str = "../TimingDAQ_mod/NetScopeStandaloneDat2Root"
    preprocessor_config: str = "configs/Keysight_v01.config"

    # Configs
    preprocessor_save_waveforms: bool = True
    overwrite_h5_files_on_pc: bool = False #!!!!!!!!!!!


class KeithleyConfig:
    '''Below are explanations of KeithleyConfig attributes: <br>
    • bias_voltages:        Bias voltages that the Keithley power supply will apply in order. Values are in [Volts]. <br>
    '''

    bias_voltages = [
        -119, -118, -117, -116, -115, 
        -114, -113, -112, -111, -110, 
        -109,]

    bias_voltages = [-109, -110, -111, -112, -113, -114, -115, -116, -117, -118, -119]