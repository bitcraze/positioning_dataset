# -*- coding: utf-8 -*-
"""
plotting lh angles
"""
import cfusdlog
import matplotlib.pyplot as plt
import argparse
import numpy as np


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_usd")
    args = parser.parse_args()

    # to fine tune the time difference between PC and CF
    time_offset = 0

    posStr = 'lighthouse'
    # posStr = 'stateEstimate'

    # decode binary log data
    data_usd = cfusdlog.decode(args.file_usd)

    # extract raw data
    cf_start_time = data_usd['estimatorEnqueuePosition']['timestamp'][0]
    time_usd = (np.array(data_usd['estimatorEnqueuePosition']['timestamp']) - cf_start_time) / 1000
    idx = np.argwhere(time_usd > 0)[0][0] + time_offset
    time_usd = time_usd[idx:]
    pos_usd = np.stack((
        data_usd['estimatorEnqueuePosition']['x'][idx:],
        data_usd['estimatorEnqueuePosition']['y'][idx:],
        data_usd['estimatorEnqueuePosition']['z'][idx:]), axis=1)

    # new figure
    plt.figure(0)

    plt.subplot(4, 1, 1)
    plt.scatter(time_usd, pos_usd[:,0], label='LH')
    plt.xlabel('Time [s]')
    plt.ylabel('X [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(4, 1, 2)
    plt.scatter(time_usd, pos_usd[:,1], label='LH')
    plt.xlabel('Time [s]')
    plt.ylabel('Y [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(4, 1, 3)
    plt.scatter(time_usd, pos_usd[:,2], label='LH')
    plt.xlabel('Time [s]')
    plt.ylabel('Z [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    ax1 = plt.subplot(4, 1, 4)
    t = (np.array(data_usd['lhAngle']['timestamp']) - cf_start_time) / 1000
    num_sensors = 4
    num_lh = 2
    num_sweeps = 2
    d = np.array(data_usd['lhAngle']['sensor']) * num_lh * num_sweeps + \
        np.array(data_usd['lhAngle']['basestation']) * num_sweeps + \
        np.array(data_usd['lhAngle']['sweep'])
    idx = np.argwhere(t > 0)[0][0] + 4
    ax1.scatter(t[idx:], d[idx:])
    ax1.set_ylabel('# Received LH Angle From ID')

    plt.show()

