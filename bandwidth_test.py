#!/usr/bin/env python
# This is a script to estimate BLE bandwith for the psylink device.
# Usages:
#     python3 bandwidth_test.py [bluetooth_backend] [address]
#     python3 bandwithh_test.py list
import random

import numpy
#import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import psylink.bluetooth
import psylink.protocol
import time
import sys

RUN_SECONDS = 60000000
def makeGraph(data,i):
    plt.plot(xs, data, label=f"EMG {i}")
    # plt.plot(xs,yss)
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title("A simple line graph")
    plt.show()
if 'list' in sys.argv[1:]:
    print('\n'.join(psylink.bluetooth.BACKENDS))
    sys.exit(0)
try:
    BackendClass = psylink.bluetooth.BACKENDS[sys.argv[1]]
except IndexError:
    name, BackendClass = list(psylink.bluetooth.BACKENDS.items())[0]
    print("Warning: Using default BLE backend %s." % name)


if len(sys.argv) > 2:
    address = sys.argv[2]
    backend = BackendClass(address=address)
else:
    backend = BackendClass()

backend.connect()
backend.thread_start(disconnect_on_stop=True)


decoder = psylink.protocol.BLEDecoder()
channels = decoder.decode_channel_count(backend.read_channels())

t_next = time.time() + .01
t_end = time.time() + RUN_SECONDS
samples_per_second = 0
bytes_per_second = 0
packets_per_second = 0
max_bytes_in_a_packet = 0


xs = []

yss = []
ys = [[],[],[],[],[],[],[],[]]

count =0
print("starting")
try:
    t_start = time.time()
    flexed = False
    flex_target = 1
    while time.time() < t_end:
        count+=1
        packet = backend.pipe.get()
        decoded = decoder.decode_packet(packet)
        all_samples = decoded['samples']
        samp_sums = sum(abs(number) for number in all_samples[2])
        all_sum = samp_sums / len(all_samples[2])
        # avg = numpy.mean([[abs(x) for x in samp[:8]] for samp in decoded['samples']['array']])
        # print(all_sum)
        #What if we look for a change in highs and lows and some how disregard the points when it fluxates maybe write some ai code
        if flexed and all_sum < flex_target:
            print('unflex')
            flexed = False
        if not flexed and all_sum > flex_target:
            print('flex')
            flexed = True
        if count%1500:
            print(f"all_sum:{all_sum}, sampsums: {samp_sums}")
            timeDif = time.time()-t_start
            # print(f"diff:{timeDif} , Count: {count},  Rate: {count/max(1, int(timeDif))}")
        continue
        max_bytes_in_a_packet = max(max_bytes_in_a_packet, len(packet['content']))
        packets_per_second += 100
        bytes_per_second += len(packet)
        samples_per_second += len(decoded['samples'])





        if time.time() > t_next:
            print(f"FPS: {packets_per_second}, BPS: {bytes_per_second}, BPP: {max_bytes_in_a_packet}, SPS: {samples_per_second} * {channels} = {samples_per_second * channels}")
            #for i in range(7):


                #ys[j].append(numpy.mean(angel))

            #yss.append(numpy.mean(angel))

            t_next += .01
            packets_per_second = bytes_per_second = samples_per_second = max_bytes_in_a_packet = 0
    print("Alee")
except KeyboardInterrupt:
    print("test")


finally:
    print("End")
    backend.thread_stop()
    backend.disconnect()
