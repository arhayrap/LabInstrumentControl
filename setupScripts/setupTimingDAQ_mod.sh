ENV_NAME="$1"

# TimingDAQ setup
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
cp TimingDAQ_mod.zip ../
unzip ../TimingDAQ_mod.zip -d ../
rm ../TimingDAQ_mod.zip
cd ../TimingDAQ_mod
make -j8
