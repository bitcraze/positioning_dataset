# -*- coding: utf-8 -*-
"""
Aligning Lighthouse and motion capture data
"""
import cfusdlog
import matplotlib.pyplot as plt
import re
import argparse
import numpy as np
from rigid_transform import compute_rigid_transform

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_usd")
    parser.add_argument("file_mocap")
    args = parser.parse_args()

    # decode binary log data
    data_usd = cfusdlog.decode(args.file_usd)
    # print(data_usd)

    # read mocap data
    # start of mocap alignment is zero, since that is the first frame we get data
    data_mocap = np.loadtxt(args.file_mocap, delimiter=',', skiprows=1, ndmin=2)
    time_mocap = (data_mocap[:,0] - data_mocap[0,0])/1000
    pos_mocap = data_mocap[:,1:4]

    # to fine tune the time difference between PC and CF
    best_time_offset = None
    best_error = np.inf
    time_offset_ms = -100
    done = False
    while True:
        # find start of usd log for alignment
        assert(data_usd['activeMarkerModeChanged']['mode'][0] == 1)
        cf_start_time = data_usd['activeMarkerModeChanged']['timestamp'][0] + time_offset_ms
        # time_fixedFrequency = (np.array(data_usd['fixedFrequency']['timestamp']) - cf_start_time) / 1000
        # idx = np.argwhere(time_fixedFrequency > 0)[0][0] + time_offset

        # extract raw data
        time_usd = (np.array(data_usd['estimatorEnqueuePosition']['timestamp']) - cf_start_time) / 1000
        idx = np.argwhere(time_usd > 0)[0][0]
        time_usd = time_usd[idx:]
        pos_usd = np.stack((
            data_usd['estimatorEnqueuePosition']['x'][idx:],
            data_usd['estimatorEnqueuePosition']['y'][idx:],
            data_usd['estimatorEnqueuePosition']['z'][idx:]), axis=1)

        # merge dataset by interpolating mocap data
        pos_mocap_merged = np.stack((
            np.interp(time_usd, time_mocap, pos_mocap[:,0]),
            np.interp(time_usd, time_mocap, pos_mocap[:,1]),
            np.interp(time_usd, time_mocap, pos_mocap[:,2])), axis=1)


        # compute spatial alignment
        # R, t = compute_rigid_transform(pos_usd[sensorsUsed > 0], pos_mocap_merged[sensorsUsed > 0])
        # print(pos_usd.shape, pos_mocap_merged.shape)
        R, t = compute_rigid_transform(pos_usd, pos_mocap_merged)
        pos_usd = pos_usd @ R.T + t

        error = np.mean(np.linalg.norm(pos_usd - pos_mocap_merged, axis=1))
        if done:
            break
        if error < best_error:
            best_error = error
            best_time_offset = time_offset_ms
        time_offset_ms += 5
        if time_offset_ms > 100:
            time_offset_ms = best_time_offset
            done = True

    print("Found time offset: ", time_offset_ms)

    # new figure
    fig, ax = plt.subplots(5,1,sharex=True)

    ax[0].scatter(time_usd, pos_usd[:,0], label='LH')
    ax[0].plot(time_mocap, pos_mocap[:,0], 'g-', label='Mocap')
    # plt.plot(time_usd, pos_usd[:,0] - pos_mocap_merged[:,0], '-', label='error')
    ax[0].set_xlabel('Time [s]')
    ax[0].set_ylabel('X [m]')
    ax[0].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[1].scatter(time_usd, pos_usd[:,1], label='LH')
    ax[1].plot(time_mocap, pos_mocap[:,1], 'g-', label='Mocap')
    # ax[1].plot(time_usd, pos_usd[:,1] - pos_mocap_merged[:,1], '-', label='error')
    ax[1].set_xlabel('Time [s]')
    ax[1].set_ylabel('Y [m]')
    ax[1].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[2].scatter(time_usd, pos_usd[:,2], label='LH')
    ax[2].plot(time_mocap, pos_mocap[:,2], 'g-', label='Mocap')
    # ax[2].plot(time_usd, pos_usd[:,2] - pos_mocap_merged[:,2], '-', label='error')
    ax[2].set_xlabel('Time [s]')
    ax[2].set_ylabel('Z [m]')
    ax[2].legend(loc=9, ncol=3, borderaxespad=0.)

    # ax1 = plt.subplot(6, 1, 4)
    # ax1.plot(time_usd, sensorsUsed, '-')
    # ax1.set_ylabel('# sensors used')
    # ax2 = ax1.twinx()
    # ax2.plot(time_usd, delta, 'g-')
    # ax2.set_ylabel('LH Delta')
    # plt.xlabel('Time [s]')

    t = (np.array(data_usd['lhAngle']['timestamp']) - cf_start_time) / 1000
    num_sensors = 4
    num_lh = 2
    num_sweeps = 2
    d = np.array(data_usd['lhAngle']['sensor']) * num_lh * num_sweeps + \
        np.array(data_usd['lhAngle']['basestation']) * num_sweeps + \
        np.array(data_usd['lhAngle']['sweep'])
    idx = np.argwhere(t > 0)[0][0] + 4
    ax[3].scatter(t[idx:], d[idx:])
    ax[3].set_ylabel('# Received LH Angle From ID')

    error = np.linalg.norm(pos_usd - pos_mocap_merged, axis=1)
    ax[4].scatter(time_usd, error, label='LH')
    print("Euc. Error: Avg: {} Max: {}".format(np.mean(error), np.max(error)))

    # time = (np.array(data_usd['fixedFrequency']['timestamp']) - cf_start_time) / 1000
    # idx = np.argwhere(time > 0)[0][0]
    # time = time[idx:]
    # pos_stateEstimate = np.stack((
    #     data_usd['fixedFrequency']['stateEstimate.x'][idx:],
    #     data_usd['fixedFrequency']['stateEstimate.y'][idx:],
    #     data_usd['fixedFrequency']['stateEstimate.z'][idx:]), axis=1)
    # pos_mocap_merged = np.stack((
    #     np.interp(time, time_mocap, pos_mocap[:,0]),
    #     np.interp(time, time_mocap, pos_mocap[:,1]),
    #     np.interp(time, time_mocap, pos_mocap[:,2])), axis=1)
    # R, t = compute_rigid_transform(pos_stateEstimate, pos_mocap_merged)
    # pos_stateEstimate = pos_stateEstimate @ R.T + t
    # ax[4].plot(time, np.linalg.norm(pos_stateEstimate - pos_mocap_merged, axis=1), label='State Estimate')

    ax[4].set_xlabel('Time [s]')
    ax[4].set_ylabel('Euclidean Error [m]')

    # plt.subplot(2, 1, 2)
    # plt.plot(data_mocap[:,0], data_mocap[:,4], '-', label='z')
    # plt.xlabel('RTOS Ticks [ms]')
    # plt.ylabel('yaw [deg]')
    # plt.legend(loc=9, ncol=3, borderaxespad=0.)

    # plt.show()

    # # new figure
    # plt.figure(0)

    # plt.subplot(2, 1, 1)
    # plt.plot(data_usd['tick'], data_usd['gyro.z'], '-', label='z')
    # plt.xlabel('RTOS Ticks [ms]')
    # plt.ylabel('Gyroscope [°/s]')
    # plt.legend(loc=9, ncol=3, borderaxespad=0.)

    # plt.subplot(2, 1, 2)
    # plt.plot(data_mocap[:,0], data_mocap[:,4], '-', label='z')
    # plt.xlabel('RTOS Ticks [ms]')
    # plt.ylabel('yaw [deg]')
    # plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.show()