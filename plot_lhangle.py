# -*- coding: utf-8 -*-
"""
plotting lh angles
"""
import cfusdlog
import matplotlib.pyplot as plt
import argparse
import numpy as np

num_sensors = 4
num_lh = 2
num_sweeps = 2

def compute_measurement_id(sensor, basestation, sweep):
    return sensor * num_lh * num_sweeps + \
            basestation * num_sweeps + \
            sweep


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_usd")
    args = parser.parse_args()

    # to fine tune the time difference between PC and CF
    time_offset = 0

    # decode binary log data
    data_usd = cfusdlog.decode(args.file_usd)

    print(data_usd['lhUartFrame'])
    exit()

    # # extract raw data
    cf_start_time = data_usd['lhAngle']['timestamp'][0]
    # time_usd = (np.array(data_usd['lhCrossingBeam']['timestamp']) - cf_start_time) / 1000
    # idx = np.argwhere(time_usd > 0)[0][0] + time_offset
    # time_usd = time_usd[idx:]
    # pos_usd = np.stack((
    #     data_usd['lhCrossingBeam']['x'][idx:],
    #     data_usd['lhCrossingBeam']['y'][idx:],
    #     data_usd['lhCrossingBeam']['z'][idx:]), axis=1)

    # new figure
    fig, ax = plt.subplots(5,1,sharex=True)

    # ax[0].scatter(time_usd, pos_usd[:,0], label='LH')
    # ax[0].set_ylabel('X [m]')
    # ax[0].legend(loc=9, ncol=3, borderaxespad=0.)

    # ax[1].scatter(time_usd, pos_usd[:,1], label='LH')
    # ax[1].set_ylabel('Y [m]')
    # ax[1].legend(loc=9, ncol=3, borderaxespad=0.)

    # ax[2].scatter(time_usd, pos_usd[:,2], label='LH')
    # ax[2].set_ylabel('Z [m]')
    # ax[2].legend(loc=9, ncol=3, borderaxespad=0.)

    t = (np.array(data_usd['lhAngle']['timestamp']) - cf_start_time) / 1000
    d = compute_measurement_id(np.array(data_usd['lhAngle']['sensor']),
                                np.array(data_usd['lhAngle']['basestation']),
                                np.array(data_usd['lhAngle']['sweep']))
    idx = np.argwhere(t > 0)[0][0] + 4
    ax[3].scatter(t[idx:], d[idx:])
    ax[3].set_ylabel('# Received LH Angle From ID')

    t = (np.array(data_usd['lhUartFrame']['timestamp']) - cf_start_time) / 1000
    print(np.max(np.array(data_usd['lhUartFrame']['sensor'])))
    print(np.max(np.array(data_usd['lhUartFrame']['basestation'])))
    print(np.max(np.array(data_usd['lhUartFrame']['sweep'])))
    d = compute_measurement_id(np.array(data_usd['lhUartFrame']['sensor']),
                                np.array(data_usd['lhUartFrame']['basestation']),
                                np.array(data_usd['lhUartFrame']['sweep']))
    idx = np.argwhere(t > 0)[0][0] + 4
    ax[4].scatter(t[idx:], d[idx:])
    ax[4].set_ylabel('# Received LH Angle From ID')

    ax[-1].set_xlabel('Time [s]')

    plt.show()

    fig, ax = plt.subplots(16,1,sharex=True)
    angles = np.array(data_usd['lhAngle']['angle'])
    for sensor in range(num_sensors):
        for lh in range(num_lh):
            for sweep in range(num_sweeps):
                s = compute_measurement_id(sensor, lh, sweep)
                ax[s].plot(t[d==s], angles[d==s],'.-')
                ax[s].set_title("Sensor: {}, LH {}, Sweep: {}".format(sensor, lh, sweep))
    plt.show()
