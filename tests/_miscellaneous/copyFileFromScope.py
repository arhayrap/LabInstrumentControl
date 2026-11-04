from classes.KeysightUXR_class import InfiniiumScope
import time

initial = time.time()
scope = InfiniiumScope()

files = [
    r"C:\Users\Public\Documents\Infiniium\Waveforms\RT_3x3_vb113v_mcp4300_ch1.h5",
    r"C:\Users\Public\Documents\Infiniium\Waveforms\RT_3x3_vb113v_mcp4300_ch2.h5"
    ]

for file in files:

    scope.iCopyFile(
        scope_filepath=file,
        pc_output_directory="./",
        chunk_size_bytes=512*1024,
        overwrite_existing=True
    )

scope.iClose()
print(f"\n\n\n Everything took {time.time()-initial} seconds.")

