# -*- coding: utf-8 -*-
"""
compute jitter
"""
from operator import pos
import cfusdlog
import argparse
import numpy as np
import glob

def readDataUSD(filename):
    data = cfusdlog.decode(filename)
    if 'lhCrossingBeam' in data:
        t = data['lhCrossingBeam']['timestamp'] / 1000
        pos = np.stack((
            data['lhCrossingBeam']['x'],
            data['lhCrossingBeam']['y'],
            data['lhCrossingBeam']['z']), axis=1)
    else:
        t = data['fixedFrequency']['timestamp'] / 1000
        pos = np.stack((
            data['fixedFrequency']['stateEstimate.x'],
            data['fixedFrequency']['stateEstimate.y'],
            data['fixedFrequency']['stateEstimate.z']), axis=1)

    t_diff = np.diff(t)
    pos_diff = np.diff(pos, axis=0)
    return t_diff, pos_diff


def readDataMocap(filename):
    data = np.load(filename)
    t = data[:,0] / 1000
    pos = data[:, 1:4]

    t_diff = np.diff(t)
    pos_diff = np.diff(pos, axis=0)

    # filter nan values
    t_diff = t_diff[~np.isnan(pos_diff[:,0])]
    pos_diff = pos_diff[~np.isnan(pos_diff[:,0])]

    return t_diff, pos_diff


def readData(filename):
    if "mocap" in filename:
        return readDataMocap(filename)
    else:
        return readDataUSD(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()

    for pattern in ["log*", "mocap*"]:
        print("Analyzing pattern: {}".format(pattern))
        t_diff = np.empty(0)
        pos_diff = np.empty((0,3))
        for file in glob.glob(args.folder + "/" + pattern):
            td, pd = readData(file)
            t_diff = np.append(t_diff, td)
            pos_diff = np.append(pos_diff, pd, axis=0)

        freq = 1 / t_diff
        print("Freq [Hz]: avg: {}, std: {}".format(
            np.mean(freq),
            np.std(freq)))

        distance_diff = np.linalg.norm(pos_diff, axis=1)
        jitter = np.sqrt(np.mean(distance_diff**2))
        print("Jitter [mm]: {} (samples: {})".format(jitter*1000, len(distance_diff)))

        

