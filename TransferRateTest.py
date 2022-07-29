#########################################################################
# Script to determine transfer rate on 2 Series MSO (1.42.0.219)        #
# CH1 of scope should connect to probe compensation signal              #
# Prerequisites - PyVISA (1.12.0), numpy (1.23.0), matplotlib (3.5.2)   #
#########################################################################

import time # std module
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import matplotlib.pyplot as plt # http://matplotlib.org/
import numpy as np # http://www.numpy.org/

debug = 1

visa_address = 'USB::0x0699::0x0105::PQ100215::INSTR'

rm = visa.ResourceManager()
scope = rm.open_resource(visa_address)
scope.timeout = 10000 # ms
scope.encoding = 'latin_1'
scope.read_termination = '\n'
scope.write_termination = None
scope.write('*cls') # clear ESR
scope.write('header OFF') # disable attribute echo in replies

print(scope.query('*idn?'))

# prompt
input("""
ACTION:
Connect probe to oscilloscope Channel 1 and the probe compensation signal.

Press Enter to continue...
""")

# select test parameters
if(debug):
    SampleRate = 25e6
    HorizontalScale = 4e-4
    RecordLength = 125e3
    trials = 1000
    NumBytes = 1
else:
    SampleRate = int(input("Enter Sample Rate (S/s):"))
    HorizontalScale = int(input("Enter Horizontal Scale (s/div):"))
    RecordLength = int(input("Enter Record Length (#):"))
    trials = int(input("Enter Number of Trials (#):"))
    NumBytes = int(input("Enter Number of Bytes (1 or 2):"))

if NumBytes == 1:
    datatype = 'b'
else:
    datatype = 'h'

# setting configurations
scope.write('HORizontal:SAMPLERate:ANALYZemode:MINimum:VALue %s' %(SampleRate))
scope.write('HORizontal:MODE:SCAle %s' %(HorizontalScale))
scope.write('HORizontal:MODE MANual')
scope.write('HORizontal:MODE:RECOrdlength %s' %(RecordLength))

# curve configuration
scope.write('data:encdg SRIBINARY') # signed integer
scope.write('data:source CH1')
scope.write('data:start 1')
acq_record = int(scope.query('horizontal:recordlength?'))
scope.write('data:stop {}'.format(acq_record))
scope.write('wfmoutpre:byt_n {}'.format(NumBytes)) # 1 byte per sample

total = 0
times = []

for(x) in range(trials):
    # acquisition
    scope.write('acquire:state OFF') # stop
    scope.write('acquire:stopafter SEQUENCE;state ON') # single
    t5 = time.perf_counter()
    r = scope.query('*opc?')
    t6 = time.perf_counter()

    # data query
    t7 = time.perf_counter()
    bin_wave = scope.query_binary_values('curve?', datatype, container=np.array, chunk_size = 1024**2)
    t8 = time.perf_counter()
    print('Transfer Time {}: {} s'.format(x + 1, t8 - t7))
    total += t8 - t7
    times.append(t8 - t7)

print("Average Transfer Time: {} s".format(total / trials))

'''
# error checking
r = int(scope.query('*esr?'))
print('event status register: 0b{:08b}'.format(r))
r = scope.query('allev?').strip()
print('all event messages: {}'.format(r))
'''

# disconnect
scope.close()
rm.close()

# plots transfer times
plt.plot(list(range(1, trials + 1)), times)
plt.title('Waveform Transfer Rate') # plot label
plt.xlabel('Trial (#)') # x label
plt.ylabel('Time (s)') # y label
plt.show()
