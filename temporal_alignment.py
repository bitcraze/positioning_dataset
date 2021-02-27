# -*- coding: utf-8 -*-
"""
Aligning Lighthouse and motion capture data
"""
import CF_functions as cff
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
    data_usd = cff.decode(args.file_usd)

    # read mocap data
    data_mocap = np.loadtxt(args.file_mocap, delimiter=',', skiprows=1, ndmin=2)

    # find first jump in gyrodata for alignment
    diff = np.abs(np.diff(data_usd['gyro.z']))
    idx_usd = np.argwhere(diff > 50)[0][0]
    # print(idx_usd)

    # find first jump in mocap yaw data for alignment
    diff = np.abs(np.diff(data_mocap[:,4]))
    idx_mocap = np.argwhere(diff > 0.02)[0][0]
    # print(idx_mocap)
    # exit()

    # extract raw data
    time_usd = (data_usd['tick'][idx_usd:] - data_usd['tick'][idx_usd])/1000
    pos_usd = np.stack((
        data_usd['lighthouse.x'][idx_usd:],
        data_usd['lighthouse.y'][idx_usd:],
        data_usd['lighthouse.z'][idx_usd:]), axis=1)

    time_mocap = (data_mocap[idx_mocap:,0] - data_mocap[idx_mocap,0])
    pos_mocap = data_mocap[idx_mocap:,1:4]

    # merge dataset by interpolating mocap data
    pos_mocap_merged = np.stack((
        np.interp(time_usd, time_mocap, pos_mocap[:,0]),
        np.interp(time_usd, time_mocap, pos_mocap[:,1]),
        np.interp(time_usd, time_mocap, pos_mocap[:,2])), axis=1)


    # compute spatial alignment
    R, t = compute_rigid_transform(pos_usd, pos_mocap_merged)
    pos_usd = pos_usd @ R.T + t

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

    plt.subplot(4, 1, 1)
    plt.plot(time_usd, pos_usd[:,0], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,0], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,0] - pos_mocap_merged[:,0], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('X [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(4, 1, 2)
    plt.plot(time_usd, pos_usd[:,1], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,1], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,1] - pos_mocap_merged[:,1], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('Y [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    plt.subplot(4, 1, 3)
    plt.plot(time_usd, pos_usd[:,2], '-', label='LH')
    plt.plot(time_usd, pos_mocap_merged[:,2], '-', label='Mocap')
    plt.plot(time_usd, pos_usd[:,2] - pos_mocap_merged[:,2], '-', label='error')
    plt.xlabel('Time [s]')
    plt.ylabel('Z [m]')
    plt.legend(loc=9, ncol=3, borderaxespad=0.)

    ax1 = plt.subplot(4, 1, 4)
    ax1.plot(time_usd, data_usd['lighthouse.sensorsUsed'][idx_usd:], '-')
    ax1.set_ylabel('# sensors used')
    ax2 = ax1.twinx()
    ax2.plot(time_usd, data_usd['lighthouse.delta'][idx_usd:], 'g-')
    ax2.set_ylabel('LH Delta')
    plt.xlabel('Time [s]')

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