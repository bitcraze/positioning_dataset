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

def process(time_offset_start, time_offset_end):
    global error
    global time_usd
    global pos_usd
    global pos_mocap_merged
    global cf_start_time
    global time_scale
    global valid
    global delta

    # find start of usd log for alignment
    assert(data_usd['activeMarkerModeChanged']['mode'][0] == 1)
    assert(data_usd['activeMarkerModeChanged']['mode'][1] == 0)
    cf_start_time = data_usd['activeMarkerModeChanged']['timestamp'][0] + time_offset_start
    cf_end_time = data_usd['activeMarkerModeChanged']['timestamp'][1] + time_offset_end
    cf_duration = cf_end_time - cf_start_time
    mocap_duration = time_mocap[-1] * 1000
    time_scale = mocap_duration / cf_duration
    # print(mocap_duration, cf_duration, time_scale)
    # exit()
    # assert(abs(mocap_duration - cf_duration) < 0.02)
    # print(cf_start_time, cf_end_time, cf_end_time - cf_start_time)
    # print(data_mocap[:,0] - data_mocap[0,0])
    # exit()

    # time_fixedFrequency = (np.array(data_usd['fixedFrequency']['timestamp']) - cf_start_time) / 1000
    # idx = np.argwhere(time_fixedFrequency > 0)[0][0] + time_offset

    # extract raw data
    if 'lhCrossingBeam' in data_usd and len(data_usd['lhCrossingBeam']['timestamp']) > 0:
        t = np.array(data_usd['lhCrossingBeam']['timestamp'])
        argwhere = np.argwhere(t >= cf_start_time)
        if len(argwhere) > 0:
            idx = argwhere[0][0]
        else:
            idx = 0
        argwhere = np.argwhere(t >= cf_end_time)
        if len(argwhere) > 0:
            idxEnd = argwhere[0][0]
        else:
            idxEnd = -1
        time_usd = (t - cf_start_time) / 1000 * time_scale
        time_usd = time_usd[idx:idxEnd]
        pos_usd = np.stack((
            data_usd['lhCrossingBeam']['x'][idx:idxEnd],
            data_usd['lhCrossingBeam']['y'][idx:idxEnd],
            data_usd['lhCrossingBeam']['z'][idx:idxEnd]), axis=1)
        delta = data_usd['lhCrossingBeam']['delta'][idx:idxEnd]
    else:
        t = np.array(data_usd['fixedFrequency']['timestamp'])
        argwhere = np.argwhere(t >= cf_start_time)
        if len(argwhere) > 0:
            idx = argwhere[0][0]
        else:
            idx = 0
        argwhere = np.argwhere(t >= cf_end_time)
        if len(argwhere) > 0:
            idxEnd = argwhere[0][0]
        else:
            idxEnd = -1
        time_usd = (t - cf_start_time) / 1000 * time_scale
        time_usd = time_usd[idx:idxEnd]
        pos_usd = np.stack((
            data_usd['fixedFrequency']['stateEstimate.x'][idx:idxEnd],
            data_usd['fixedFrequency']['stateEstimate.y'][idx:idxEnd],
            data_usd['fixedFrequency']['stateEstimate.z'][idx:idxEnd]), axis=1)
        delta = None

    # merge dataset by interpolating mocap data
    pos_mocap_merged = np.stack((
        np.interp(time_usd, time_mocap, pos_mocap[:,0]),
        np.interp(time_usd, time_mocap, pos_mocap[:,1]),
        np.interp(time_usd, time_mocap, pos_mocap[:,2])), axis=1)


    # compute spatial alignment
    # R, t = compute_rigid_transform(pos_usd[sensorsUsed > 0], pos_mocap_merged[sensorsUsed > 0])
    # print(pos_usd.shape, pos_mocap_merged.shape)
    valid = ~np.isnan(pos_mocap_merged).any(axis=1)
    R, t = compute_rigid_transform(pos_usd[valid], pos_mocap_merged[valid])
    pos_usd = pos_usd @ R.T + t

    error = np.mean(np.linalg.norm(pos_usd[valid] - pos_mocap_merged[valid], axis=1))


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
    # data_mocap = np.loadtxt(args.file_mocap, delimiter=',', skiprows=1, ndmin=2)
    data_mocap = np.load(args.file_mocap)
    time_mocap = (data_mocap[:,0] - data_mocap[0,0])/1000
    pos_mocap = data_mocap[:,1:4]

    # to fine tune the time difference between PC and CF
    best_time_offset_start = None
    best_time_offset_end = None
    best_error = np.inf
    # time_offset_ms = -100
    # done = False
    # while True:
    for time_offset_start in np.arange(-100,100,5):
        for time_offset_end in np.arange(-100,100,5):
            process(time_offset_start, time_offset_end)
            # print(time_offset_ms, error)
            # if done:
                # break
            if error < best_error:
                best_error = error
                best_time_offset_start = time_offset_start
                best_time_offset_end = time_offset_end
                # print(best_error, best_time_offset_start, best_time_offset_end)
            # time_offset_ms += 5
            # if time_offset_ms > 100:
                # time_offset_ms = best_time_offset
                # done = True

    print("Found time offset: ", best_time_offset_start, best_time_offset_end)
    process(best_time_offset_start, best_time_offset_end)

    # new figure
    fig, ax = plt.subplots(5,1,sharex=True)

    ax[0].scatter(time_usd, pos_usd[:,0], label='LH')
    ax[0].plot(time_mocap, pos_mocap[:,0], 'g-', label='Mocap')
    ax2 = ax[0].twinx()
    ax2.plot(time_usd, pos_usd[:,0] - pos_mocap_merged[:,0], 'r', label='error')
    ax[0].set_xlabel('Time [s]')
    ax[0].set_ylabel('X [m]')
    ax[0].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[1].scatter(time_usd, pos_usd[:,1], label='LH')
    ax[1].plot(time_mocap, pos_mocap[:,1], 'g-', label='Mocap')
    ax2 = ax[1].twinx()
    ax2.plot(time_usd, pos_usd[:,1] - pos_mocap_merged[:,1], 'r', label='error')
    ax[1].set_xlabel('Time [s]')
    ax[1].set_ylabel('Y [m]')
    ax[1].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[2].scatter(time_usd, pos_usd[:,2], label='LH')
    ax[2].plot(time_mocap, pos_mocap[:,2], 'g-', label='Mocap')
    ax2 = ax[2].twinx()
    ax2.plot(time_usd, pos_usd[:,2] - pos_mocap_merged[:,2], 'r', label='error')
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

    t = (np.array(data_usd['lhAngle']['timestamp']) - cf_start_time) / 1000 * time_scale
    num_sensors = 4
    num_lh = 2
    num_sweeps = 2
    d = np.array(data_usd['lhAngle']['sensor']) * num_lh * num_sweeps + \
        np.array(data_usd['lhAngle']['basestation']) * num_sweeps + \
        np.array(data_usd['lhAngle']['sweep'])
    idx = np.argwhere(t > 0)[0][0]
    ax[3].scatter(t[idx:], d[idx:])
    ax[3].set_ylabel('# Received LH Angle From ID')

    error = np.linalg.norm(pos_usd - pos_mocap_merged, axis=1)
    ax[4].scatter(time_usd, error, label='LH')
    if delta is not None:
        ax2 = ax[4].twinx()
        ax2.plot(time_usd, delta, 'r.')
    print("Euc. Error: Avg: {} Max: {}".format(np.mean(error[valid]), np.max(error[valid])))

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

    #
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    p3d = ax.scatter(pos_mocap_merged[valid,0], pos_mocap_merged[valid,1], pos_mocap_merged[valid,2], s=30, c=error[valid], cmap = cm.coolwarm)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    fig.colorbar(p3d, label='Euclidean Error [m]')
    plt.show()