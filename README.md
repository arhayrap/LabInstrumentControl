### Note
The finished scripts are `kApplication.py`, `KeysightUXR_class.py`, `Keithley2410_class.py`, `convertH5ToROOT.py`, `TimingDAQ_mod.zip`.
This is more of a tool for communicating with the lab devices.
Also, there is a script for automated bias voltage scan with Keysight UXR 0104B oscilloscope and Keithley2410 power supply.

### 0. Introduction:

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

            - TimingDAQ preprocessed files (with `amp, LP2_XX, t_peak, ...`).

- **Current/Voltage/time** logging scripts (for example for LGAD leakage current gradual increasing studies).


### 1. How to set up.

1. Install **Keysight IO Libraries**: https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html

2. Clone the repository into an empty folder:
~~~bash
git clone https://github.com/SamvelAghavelyan/LabInstrumentControl
~~~

Or just download the `.zip` and unzip it into an empty folder.
So, in the end, the folder should look like this:
```
MyProjectFolder
└── LabInstrumentControl
```

3. Next step: **full setup/initialization** from scratch (RECOMMENDED for cleaner use). 
- Think of a conda environment name (I will call it `autodaq`),
- `cd` into `LabInstrumentControl` directory (such that `./` is `LabInstrumentControl`),
- Run the `fullsetup_inDevelopment.sh` script:
~~~bash
./fullsetup_inDevelopment.sh autodaq
~~~

This will create a conda environment with required modules and packages, and automatically compile the ```TimingDAQ``` preprocessors adjusted for these tools (```Appendix 1```).

- Check the project directory structure. Should look like this:
```
MyProjectFolder
├── 0_RawData_h5
├── 1_ConvertedRoots
├── 2_PreprocessedRoots
├── LabInstrumentControl
└── TimingDAQ_mod
```
- See `Appendix 3` to know what each folder is for.

### 2. How to use this tool.

- You'll need to set up Keithley 2410 communication (see `Appendix 4` and `Appendix 5` for directions).

The main script for automatic DAQ is ```autoDAQ_template.py```. I designed it to be as intuitive, configurable and modular as I could imagine within the time allocated for the project (including the testing, and other tasks too). You can find detailed documentation on how to use ```Keysight UXR0104B``` and ```Keithley 2410``` power supply for ```autoDAQ``` in the configs/```configTemplate.py``` file.

About how to run this script: 
- Copy ```config_preprocessor_template.config``` file into your workspace and adjust it to your setup.
- Copy ```config_template.py``` into your workspace (inside ```LabInstrumentControl```) and rename it. Open it in VS Code, or any other editor, and change the configurations as you want. Make sure to specify the preprocessor config path you created in the previous step in the your ```autoDAQ``` config file.
- Copy ```autoDAQ_template.py``` into your workspace, change the ```import ... as MyConfig``` part to your new config file.
- Open terminal (in VS Code or just a simple terminal). Make sure you ```cd``` into ```LabInstrumentControl``` (so that ```./``` is ```LabInstrumentControl```). Start the DAQ with this type of bash command (of course, you need to adjust the paths), specifying the number of CPUs you want to use for preprocessing :
~~~bash
python ./workspace_2ChannelSetup2026/autoDAQ.py --workers 4
~~~



### Appendix 1: About ```TimingDAQ_mod```
This is based on the original ```TimingDAQ``` scripts with minor changes. The preprocessor will accept (and expects) the following arguments:

- Usual (original ```TimingDAQ``` preprocessors):
    - ```--input_file="/path/to/your/converted/root/file"```
    - ```--config="/path/to/your/config/file"```
    - ```--output_file"/path/to/your/intended/preprocessed/root/file"```
    - ```--save_meas=true``` or ```--save_meas=false``` ― save waveforms (raw data) or not
    - ```--verbose=true``` or ```--verbose=false``` ― self-explanatory

- Additional arguments (now only in this repo's ```TimingDAQ_mod```).    
    - ```--num_channels=2``` ― default: ```2```,
    - ```--num_samples=5120``` ― default: ```5120```.


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


### Appendix 4: Connecting to Keithley 2410 using RS232 (recommended).
It should be pretty straightforward. Connect the RS232 cable to Keithley 2410 rear RS232 port and PC rear RS232 port.
Make sure that communication is setup correctly on Keithley:

- Press front panel `Menu` $\rightarrow$ `Communication` $\rightarrow$ `RS-232`
    
    - `Baud Rate` $\rightarrow$ `9600`
    - `Bits` $\rightarrow$ `8`
    - `Parity` $\rightarrow$ `None`
    - `Terminator` $\rightarrow$ `<CR>`
    - `Flow Control` $\rightarrow$ `None`

### Appendix 5: Connecting to Keithley 2410 using GPIB (NI GPIB-USBG-HS) instead of RS232.
You most probably will need to install linux gpib (like `linux-gpib` kernel module) dependencies for Keithley 2410 communication with GPIB. 
Make sure that communication is setup correctly on Keithley:

- Press front panel `Menu` $\rightarrow$ `Communication` $\rightarrow$ `GPIB`
    
    - `Address` $\rightarrow$ `5` (or anything else - make sure you check the visa address if you do not use `5`)
    - `GPIB Protocol` $\rightarrow$ `SCPI`

Next steps:

1. Clone `linux-gpib` repository. 
~~~bash
cd ~
git clone https://github.com/coolshou/linux-gpib.git
~~~ 

2. Build the kernel drivers:
~~~bash
cd ~/linux-gpib/linux-gpib-kernel
make -j"$(nproc)"
~~~

3. Install them:
~~~bash
sudo make install
~~~

4. Load NI USB-GPIB driver:
~~~bash
sudo modprob ni_usb_gpib
~~~

5. Build and install GPIB library:
~~~bash
cd ~linux-gpib/linux-gpib-user
./configure --sysconfdir=/etc
~~~

6. After that:
~~~bash
make -j"$(nproc)"
~~~

7. Install:
~~~bash
sudo make install
~~~

8. 
~~~bash
sudo ldconfig
~~~

9. Check GPIB config:
~~~bash
nano /etc/gpib.conf
~~~

You should see: `board_type = "ni_usb_b"`. If you see other thing, change to this.

10. Find Keithley's GPIB address:
~~~bash
sudo findlisteners
~~~

Should see `Listener at pad 5`, if you set Keithley address to 5.

11. Add gpib group so your user can access the gpib utilities.
~~~bash
# First run this
sudo groupadd gpib

# Then this
sudo usermod -aG gpib "$USER"
~~~

12. Final things:
~~~bash
# 1
newgr gpib

# 2
sudo udevadm control --reload-rules

# 3
sudo udevadm trigger --action=change --subsystem-match=gpib_common

# 4
ls -l /dev/gpib0
~~~

If you see something like this: `crs-rw---- 1 root gpib ... /dev/gpib0`, after you ran the `ls ...` command, it's done.


13. Test it:

~~~python
import pyvisa

keithleyAddress = "GPIB::5::INSTR"
rm = pyvisa.ResourceManager()

keithley = rm.open_resource(keithleyAddress)
keithley.timeout = 5000
keithley.write_termination = "\n"           # use "\n" for GPIB 
keithley.read_termination = "\n"            # use "\r" for RS232 

print(keithley.query("*IDN?"))
~~~

You should see Keithley 2410's "identity". Something like: `KEITHLEY INSTRUMENTS INC., MODEL ...`

### Common problems and their solutions.
