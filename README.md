### Note
The finished scripts are `kApplication.py`, `KeysightUXR_class.py`, `Keithley2410_class.py`, `convertH5ToROOT.py`.
This is more of a tool for communicating with the lab devices.
Also, there is a script for automated bias voltage scan with Keysight UXR 0104B oscilloscope and Keithley2410 power supply.

### Cloning the repository into an empty folder:
~~~bash
git clone https://github.com/SamvelAghavelyan/LabInstrumentControl
~~~

Or just download the `.zip` and unzip it into an empty folder.
So, in the end, the folder should look like this:
```
MyProjectFolder
└── LabInstrumentControl
```

### Introduction:

In this repository you will find tools to:

- **Control Keysight oscilloscope** (written and tested for Keysight UXR Series 0104B) with a dedicated class library.
    
    - Configure channels, timebase, sequence acquisition mode, triggering.
    - Make directories, copy files, delete files.
    - etc...

- **Control Keithley 2410** with a dedicated class library.
    
    - Set voltage (in voltage mode), current (in current mode),
    - Ramping current/voltage for safer usage,
    - Measure current/voltage, 

- Control **Keithley 2410 in a terminal-based application**:
    
    - Set/measure voltage/current,
    - Ramping to a certain voltage,
    - Safe shutdown (ramp down and output off).
    - etc.

- Use autoDAQ script(s) to **automatically acquire preprocessed data from Keysight**:

    - You give the system configurations (all in one `autoDaqConfig.py` script) for:
        - Keysight oscilloscope (paths, filenames, trigger setup, timebase and channels, etc.),
        - Keithley 2410 (bias voltages),
        - PC paths for the data pipeline,
        - TimingDAQ preprocessor path and config file.
    - The system outputs:

        - `.h5` files:
        
            - raw waveform files from Keysight,
        
        - `.root` converted files:

            - just several `.h5` files combined into a single `.root` file with the structure so you can "feed" them to TimingDAQ preprocessors,

        - `.root` preprocessed files:

             TimingDAQ preprocessed files (with `amp, LP2_XX, t_peak, ...`).

- **Current/Voltage/time** logging scripts (for example for LGAD leakage current gradual increasing studies).


### Software requirements (basic):
- `python 3.12`, `numpy`, `matplotlib`, `scipy`, `pandas`, `h5py`, `pyvisa`, `pyvisa-py`, `zeroconf`, `pyyaml`, `gxx`, `root`, `uproot` are needed for full automation.

- If you want to create a new conda environment, run this (change `autodaq` to your desired conda environment name):
    ~~~bash
    sudo chmod +x setupScripts/setupCondaEnvironment.sh
    ~~~
    and then:
    ~~~bash
    setupScripts/setupCondaEnvironment.sh autodaq
    ~~~

### Setting up for Keysight.

- Install **Keysight IO Libraries**: https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html
- Make sure the library path in `LabInstrumentControl/classes/KeysightUXR_class.py` is right (by default, your installation should place it in `/opt/keysight/iolibs/libktvisa32.so`).
- Make sure the visa address matches your Keysight.
- Test the connection:
~~~python
# ----------------------------------------
# Keysight communication test.
# ----------------------------------------
from classes.KeysightUXR_class import InfiniiumScope
scope = InfiniiumScope()
print(scope.iReadIdentity())

~~~

### Setting up for Keithley.
- Connect to the Keithley using an RS232 cable.
- Press front panel `Menu` $\rightarrow$ `Communication` $\rightarrow$ `RS-232`
    
    - `Baud Rate` $\rightarrow$ `9600`
    - `Bits` $\rightarrow$ `8`
    - `Parity` $\rightarrow$ `None`
    - `Terminator` $\rightarrow$ `<CR>`
    - `Flow Control` $\rightarrow$ `None`
- Find the address of the Keithley using `pyvisa.ResourceManager`.
- Make sure the addresses match in `LabInstrumentControl/classes/Keithley2410_class.py` and your visa address.
- Test the connection:
~~~python
# ----------------------------------------
# Keithley communication test.
# ----------------------------------------
from classes.Keithley2410_class import Keithley2410
keithley = Keithley2410()
print(keithley.kReadIdentity())
~~~

Although communication using RS232 is recommended, you can use GPIB cable too. This documentation does not include instructions for that.



### How to use `autoDAQ*.py` scripts.

Note:
- The main scripts for automatic DAQ with Keysight and Keithley are `autoDAQ*.py` and `Configs*.py`. I designed it to be as intuitive, configurable and modular as I could imagine within the time allocated for the project (including the testing and analysis). You can find detailed documentation on how to configure `Keysight UXR0104B` (triggering/channels/ranges/etc.) and `Keithley 2410` (which bias voltages to scan) for automatic DAQ in the `Configs*.py` scripts.


Recommended: create a new `workspace` folder in `LabInstrumentControl` parent dirrectory and copy the files in `_templates/` to the `workspace`.

About how to run this script: 
- Copy ```preprocessor_example.config``` file into your workspace and adjust it to your setup.
- Copy ```config_template.py``` into your workspace (inside ```LabInstrumentControl```) and rename it. Open it in VS Code, or any other editor, and change the configurations as you want. Make sure to specify the preprocessor config path you created in the previous step in the your ```autoDAQ``` config file.
- Copy ```autoDAQ_template.py``` into your workspace, change the ```import ... as MyConfig``` part to your new config file.
- Open terminal (in VS Code or just a simple terminal). Make sure you ```cd``` into ```LabInstrumentControl``` (so that ```./``` is ```LabInstrumentControl```). Start the DAQ with this type of bash command (of course, you need to adjust the paths), specifying the number of CPUs you want to use for preprocessing :
~~~bash
python ./workspace_2ChannelSetup2026/autoDAQ.py --workers 4
~~~



### Appendix 1: About ```TimingDAQ_mod```
See https://github.com/SamvelAghavelyan/TimingDAQ_mod for more information.

### Appendix 2: Useful links and manuals:
- Keysight error messages: https://helpfiles.keysight.com/csg/e5072a/product_information/error_messages/error_messages.htm

- Keysight Programmer's guide: https://www.keysight.com/us/en/assets/9018-07141/programming-guides/9018-07141.pdf

- Keithley 2410 manual: https://download.tek.com/manual/2410_902_01B.pdf

- TimingDAQ: https://github.com/CMS-MTD/TimingDAQ


### Appendix 3: About folder macro-structure.
Let's see this structure (will call it macro-structure):
```
MyProjectFolder
├── 0_RawData_h5
├── 1_ConvertedRoots
├── 2_PreprocessedRoots
├── LabInstrumentControl
└── TimingDAQ_mod
```
- `MyProjectFolder` ―― the parent directory for the whole project. Every relative path is "calculated" with respect to it. This is the highest-level directory used in the project.
- `0_RawData_h5` ― the directory where all the `.h5` files (raw waveforms) from oscilloscope will be copied.
- `1_ConvertedRoots` ―― where all the **converted** `.root` files will be created (and stored). This are the products of `convertH5ToRoot.py` script. The script just combines all specified `.h5` waveform files into a `.root` file that has the structure (like `channel, time, i_evt, ...`) needed for `TimingDAQ` preprocessing.
- `2_PreprocessedRoots` ―― TiminDAQ-preprocessed (in reality - `TimingDAQ_mod`) files (with `amp, LP2_XX, t_peak, ...`).


### Common problems and their solutions.
