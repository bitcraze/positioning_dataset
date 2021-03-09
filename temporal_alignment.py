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

    posStr = 'lighthouse'
    # posStr = 'stateEstimate'

    # decode binary log data
    data_usd = cfusdlog.decode(args.file_usd)
    # print(data_usd)

    # read mocap data
    data_mocap = np.loadtxt(args.file_mocap, delimiter=',', skiprows=1, ndmin=2)

    # find start of usd log for alignment
    assert(data_usd['activeMarkerModeChanged']['mode'][0] == 1)
    data_usd_start_time = data_usd['activeMarkerModeChanged']['timestamp'][0]
    time_usd = np.array(data_usd['fixedFrequency']['timestamp'])
    idx_usd = np.argwhere(time_usd > data_usd_start_time)[0][0] + 4

    # start of mocap alignment is zero, since that is the first frame we get data
    idx_mocap = 0

    # extract raw data
    time_usd = (time_usd[idx_usd:] - time_usd[idx_usd])/1000
    pos_usd = np.stack((
        data_usd['fixedFrequency'][posStr + '.x'][idx_usd:],
        data_usd['fixedFrequency'][posStr + '.y'][idx_usd:],
        data_usd['fixedFrequency'][posStr + '.z'][idx_usd:]), axis=1)
    # sensorsUsed = np.array(data_usd['fixedFrequency']['lighthouse.sensorsUsed'][idx_usd:])
    # delta = np.array(data_usd['fixedFrequency']['lighthouse.delta'][idx_usd:])

    # remove position entries where we didn't receive LH data
    # time_usd = time_usd[sensorsUsed > 0]
    # pos_usd = pos_usd[sensorsUsed > 0]
    # delta = delta[sensorsUsed > 0]
    # sensorsUsed = sensorsUsed[sensorsUsed > 0]
    # pos_usd[sensorsUsed==0] = np.nan

    time_mocap = (data_mocap[idx_mocap:,0] - data_mocap[idx_mocap,0])/1000
    pos_mocap = data_mocap[idx_mocap:,1:4]

    # merge dataset by interpolating mocap data
    pos_mocap_merged = np.stack((
        np.interp(time_usd, time_mocap, pos_mocap[:,0]),
        np.interp(time_usd, time_mocap, pos_mocap[:,1]),
        np.interp(time_usd, time_mocap, pos_mocap[:,2])), axis=1)


    # compute spatial alignment
    # R, t = compute_rigid_transform(pos_usd[sensorsUsed > 0], pos_mocap_merged[sensorsUsed > 0])
    R, t = compute_rigid_transform(pos_usd, pos_mocap_merged)
    pos_usd = pos_usd @ R.T + t

    # pos_usd[sensorsUsed == 0] = np.nan

    # print(ret_R, ret_t)
    # exit()
    # print(pos_usd[0], R @ pos_usd[0] + t)
    # exit()
    # print(pos_usd)


    # R, residuals, rank, s = np.linalg.lstsq(pos_usd, pos_mocap_merged, rcond=None)
    # print(R, residuals, rank, s)
    # # exit()
    # pos_usd = pos_usd @ R

    # new figure
    plt.figure(0)

    plt.subplot(6, 1, 1)
    plt.plot(time_usd, pos_usd[:,0], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,0], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,0] - pos_mocap_merged[:,0], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('X [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(6, 1, 2)
    plt.plot(time_usd, pos_usd[:,1], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,1], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,1] - pos_mocap_merged[:,1], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('Y [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(6, 1, 3)
    plt.plot(time_usd, pos_usd[:,2], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,2], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,2] - pos_mocap_merged[:,2], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('Z [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    ax1 = plt.subplot(6, 1, 4)
    ax1.plot(time_usd, sensorsUsed, '-')
    ax1.set_ylabel('# sensors used')
    ax2 = ax1.twinx()
    ax2.plot(time_usd, delta, 'g-')
    ax2.set_ylabel('LH Delta')
    plt.xlabel('Time [s]')

    ax1 = plt.subplot(6, 1, 5)
    t = (np.array(data_usd['lhAngle']['timestamp']) - data_usd_start_time) / 1000
    num_sensors = 4
    num_lh = 2
    num_sweeps = 2
    d = np.array(data_usd['lhAngle']['sensor']) * num_lh * num_sweeps + \
        np.array(data_usd['lhAngle']['basestation']) * num_sweeps + \
        np.array(data_usd['lhAngle']['sweep'])
    idx = np.argwhere(t > 0)[0][0] + 4
    ax1.scatter(t[idx:], d[idx:])
    ax1.set_ylabel('# Received LH Angle From ID')

    plt.subplot(6, 1, 6)
    plt.plot(time_usd, np.linalg.norm(pos_usd - pos_mocap_merged, axis=1), '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('Euklidean Error [m]')

    # plt.subplot(2, 1, 2)
    # plt.plot(data_mocap[:,0], data_mocap[:,4], '-', label='z')
    # plt.xlabel('RTOS Ticks [ms]')
    # plt.ylabel('yaw [deg]')
    # plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.show()

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

    # plt.show()