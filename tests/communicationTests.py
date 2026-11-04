# ----------------------------------------
# Keysight communication test.
# ----------------------------------------
from classes.KeysightUXR_class import InfiniiumScope
scope = InfiniiumScope()
print(scope.iReadIdentity())



# ----------------------------------------
# Keithley communication test.
# ----------------------------------------
from classes.Keithley2410_class import Keithley2410
keithley = Keithley2410()
print(keithley.kReadIdentity())
