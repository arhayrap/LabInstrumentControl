import pyvisa
import logging

logging.basicConfig(level=logging.DEBUG)

import pyvisa

rm = pyvisa.ResourceManager('@py')

print(rm.list_resources())

scope = rm.open_resource(
    # 'VICP::192.168.0.174::INSTR'
    # 'TCPIP::192.168.0.174::5025::SOCKET'
    # "VICP::192.168.0.174::INSTR"
    # "TCPIP0::192.168.0.174::inst0::INSTR"
    "USB0::1535::4131::5003N60377::INSTR"
)

scope.timeout = 10000

print(scope.query('*IDN?'))
scope.close()
rm.close()

'''
rm = pyvisa.ResourceManager('@py')

print(rm.list_resources())

instrument = rm.open_resource(
    "USB0::1535::4131::5003N60377::0::INSTR"
)

print(instrument.query('*IDN?'))
'''