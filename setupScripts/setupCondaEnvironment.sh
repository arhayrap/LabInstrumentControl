ENV_NAME="$1"

# Creating conda environment with required packages
packages=(
    python=3.12
    numpy
    matplotlib
    scipy
    pandas
    h5py

    pyvisa
    pyvisa-py
    # gpib-ctypes # will need to install manually
    zeroconf

    pyyaml

    gxx

    root
    uproot
)

conda create --name "$ENV_NAME" -c conda-forge --override-channels \
    "${packages[@]}" -y
