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

class TemporalAlignment:
    def __init__(self, file_usd, file_mocap):
        # decode binary log data
        self.data_usd = cfusdlog.decode(file_usd)
        # print(data_usd)

        # read mocap data
        # start of mocap alignment is zero, since that is the first frame we get data
        # data_mocap = np.loadtxt(args.file_mocap, delimiter=',', skiprows=1, ndmin=2)
        self.data_mocap = np.load(file_mocap)
        self.time_mocap = (self.data_mocap[:, 0] - self.data_mocap[0, 0])/1000
        self.pos_mocap = self.data_mocap[:, 1:4]

        # to fine tune the time difference between PC and CF
        best_time_offset_start = None
        best_time_offset_end = None
        best_error = np.inf
        # time_offset_ms = -100
        # done = False
        # while True:
        for time_offset_start in np.arange(-100, 100, 5):
            for time_offset_end in np.arange(-100, 100, 5):
                error = self._process(time_offset_start, time_offset_end)
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
        self._process(best_time_offset_start, best_time_offset_end)

    def _process(self, time_offset_start, time_offset_end):
        # find start of usd log for alignment
        assert(self.data_usd['activeMarkerModeChanged']['mode'][0] == 1)
        assert(self.data_usd['activeMarkerModeChanged']['mode'][1] == 0)
        self.cf_start_time = self.data_usd['activeMarkerModeChanged']['timestamp'][0] + time_offset_start
        cf_end_time = self.data_usd['activeMarkerModeChanged']['timestamp'][1] + time_offset_end
        cf_duration = cf_end_time - self.cf_start_time
        mocap_duration = self.time_mocap[-1] * 1000
        self.time_scale = mocap_duration / cf_duration
        # print(mocap_duration, cf_duration, time_scale)
        # exit()
        # assert(abs(mocap_duration - cf_duration) < 0.02)
        # print(cf_start_time, cf_end_time, cf_end_time - cf_start_time)
        # print(data_mocap[:,0] - data_mocap[0,0])
        # exit()

        # time_fixedFrequency = (np.array(data_usd['fixedFrequency']['timestamp']) - cf_start_time) / 1000
        # idx = np.argwhere(time_fixedFrequency > 0)[0][0] + time_offset

        # extract raw data
        if 'lhCrossingBeam' in self.data_usd:
            t = self.data_usd['lhCrossingBeam']['timestamp']
            argwhere = np.argwhere(t >= self.cf_start_time)
            if len(argwhere) > 0:
                idx = argwhere[0][0]
            else:
                idx = 0
            argwhere = np.argwhere(t >= cf_end_time)
            if len(argwhere) > 0:
                idxEnd = argwhere[0][0]
            else:
                idxEnd = -1
            time_usd = (t - self.cf_start_time) / 1000 * self.time_scale
            time_usd = time_usd[idx:idxEnd]
            pos_usd = np.stack((
                self.data_usd['lhCrossingBeam']['x'][idx:idxEnd],
                self.data_usd['lhCrossingBeam']['y'][idx:idxEnd],
                self.data_usd['lhCrossingBeam']['z'][idx:idxEnd]), axis=1)
            self.delta = self.data_usd['lhCrossingBeam']['delta'][idx:idxEnd]
        else:
            t = self.data_usd['fixedFrequency']['timestamp']
            argwhere = np.argwhere(t >= self.cf_start_time)
            if len(argwhere) > 0:
                idx = argwhere[0][0]
            else:
                idx = 0
            argwhere = np.argwhere(t >= cf_end_time)
            if len(argwhere) > 0:
                idxEnd = argwhere[0][0]
            else:
                idxEnd = -1
            time_usd = (t - self.cf_start_time) / 1000 * self.time_scale
            time_usd = time_usd[idx:idxEnd]
            pos_usd = np.stack((
                self.data_usd['fixedFrequency']['stateEstimate.x'][idx:idxEnd],
                self.data_usd['fixedFrequency']['stateEstimate.y'][idx:idxEnd],
                self.data_usd['fixedFrequency']['stateEstimate.z'][idx:idxEnd]), axis=1)
            self.delta = None

        # merge dataset by interpolating mocap data
        pos_mocap_merged = np.stack((
            np.interp(time_usd, self.time_mocap, self.pos_mocap[:,0]),
            np.interp(time_usd, self.time_mocap, self.pos_mocap[:,1]),
            np.interp(time_usd, self.time_mocap, self.pos_mocap[:,2])), axis=1)


        # compute spatial alignment
        # R, t = compute_rigid_transform(pos_usd[sensorsUsed > 0], pos_mocap_merged[sensorsUsed > 0])
        # print(pos_usd.shape, pos_mocap_merged.shape)
        valid = ~np.isnan(pos_mocap_merged).any(axis=1)
        if self.delta is not None:
            valid = np.logical_and(valid, self.delta<0.1)
        else:
            pass
            # min_pos = np.array([-1.2, -0.9, 0.5])
            # max_pos = min_pos + 1.5
            # valid = np.logical_and(valid, (pos_mocap_merged > min_pos).all(axis=1))
            # valid = np.logical_and(valid, (pos_mocap_merged < max_pos).all(axis=1))
            lhAngle_time = (self.data_usd['lhAngle']['timestamp'] - self.cf_start_time) / 1000 * self.time_scale
            invalidIdx = np.argwhere(np.diff(lhAngle_time) > 0.25)
            if len(invalidIdx) > 0:
                for idx2 in invalidIdx:
                    idx = idx2[0]
                    # print(lhAngle_time[idx], lhAngle_time[idx+1])
                    valid=np.logical_and(valid, np.logical_not(np.logical_and(time_usd >= lhAngle_time[idx], time_usd <= lhAngle_time[idx+1] + 1.0)))
            # exit()
            # closest_time = np.array([np.abs(lhAngle_time - t).min() for t in time_usd])
            # print(closest_time)
            # exit()
            # valid = np.logical_and(valid, closest_time < 0.01)


        R, t = compute_rigid_transform(pos_usd[valid], pos_mocap_merged[valid])
        pos_usd = pos_usd @ R.T + t

        self.time_usd = time_usd
        self.pos_usd = pos_usd
        self.pos_mocap_merged = pos_mocap_merged
        self.valid = valid
        self.error = np.linalg.norm(
            pos_usd[valid] - pos_mocap_merged[valid], axis=1)

        return np.mean(self.error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_usd")
    parser.add_argument("file_mocap")
    args = parser.parse_args()

    r = TemporalAlignment(args.file_usd, args.file_mocap)

    # new figure
    fig, ax = plt.subplots(5,1,sharex=True)

    ax[0].scatter(r.time_usd, r.pos_usd[:,0], label='LH')
    ax[0].plot(r.time_mocap, r.pos_mocap[:,0], 'g-', label='Mocap')
    ax2 = ax[0].twinx()
    ax2.plot(r.time_usd, r.pos_usd[:,0] - r.pos_mocap_merged[:,0], 'r', label='error')
    ax2.tick_params(axis='y', colors='r')
    ax[0].set_ylabel('X [m]')
    ax[0].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[1].scatter(r.time_usd, r.pos_usd[:,1], label='LH')
    ax[1].plot(r.time_mocap, r.pos_mocap[:,1], 'g-', label='Mocap')
    ax2 = ax[1].twinx()
    ax2.plot(r.time_usd, r.pos_usd[:,1] - r.pos_mocap_merged[:,1], 'r', label='error')
    ax2.tick_params(axis='y', colors='r')
    ax[1].set_ylabel('Y [m]')
    ax[1].legend(loc=9, ncol=3, borderaxespad=0.)

    ax[2].scatter(r.time_usd, r.pos_usd[:,2], label='LH')
    ax[2].plot(r.time_mocap, r.pos_mocap[:,2], 'g-', label='Mocap')
    ax2 = ax[2].twinx()
    ax2.plot(r.time_usd, r.pos_usd[:,2] - r.pos_mocap_merged[:,2], 'r', label='error')
    ax2.tick_params(axis='y', colors='r')
    ax[2].set_ylabel('Z [m]')
    ax[2].legend(loc=9, ncol=3, borderaxespad=0.)

    t = (r.data_usd['lhAngle']['timestamp'] - r.cf_start_time) / 1000 * r.time_scale
    num_sensors = 4
    num_lh = 2
    num_sweeps = 2
    d = r.data_usd['lhAngle']['sensor'] * num_lh * num_sweeps + \
        r.data_usd['lhAngle']['basestation'] * num_sweeps + \
        r.data_usd['lhAngle']['sweep']
    idx = np.argwhere(t > 0)[0][0]
    ax[3].scatter(t[idx:], d[idx:])
    ax[3].set_ylabel('# Received LH Angle From ID')

    ax[4].scatter(r.time_usd[r.valid], r.error, label='LH')
    if r.delta is not None:
        ax2 = ax[4].twinx()
        ax2.plot(r.time_usd[r.valid], r.delta[r.valid], 'r.')
        ax2.tick_params(axis='y', colors='r')
    print("Euc. Error: Avg: {} Max: {}".format(np.mean(r.error), np.max(r.error)))

    ax[4].set_xlabel('Time [s]')
    ax[4].set_ylabel('Euclidean Error [m]')


    plt.show()

    # #
    # from mpl_toolkits.mplot3d import Axes3D
    # from matplotlib import cm
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # p3d = ax.scatter(r.pos_mocap_merged[r.valid,0], r.pos_mocap_merged[r.valid,1], r.pos_mocap_merged[r.valid,2], s=30, c=error[r.valid], cmap = cm.coolwarm)
    # ax.set_xlabel('X [m]')
    # ax.set_ylabel('Y [m]')
    # ax.set_zlabel('Z [m]')
    # fig.colorbar(p3d, label='Euclidean Error [m]')
    # plt.show()

    # data = np.concatenate((r.pos_mocap_merged[r.valid], np.atleast_2d(error).T[r.valid]), axis=1)
    # print(data.shape)
