# -*- coding: utf-8 -*-
"""
plotting the Euclidean error in 3D
"""
import matplotlib.pyplot as plt
import numpy as np
import glob
import cfusdlog

DATASETS = [
    "lh1_crossingBeam_jitter",
    "lh1_crossingBeam_move",
    "lh1_crossingBeam_flight",
    "lh1_kalman_jitter",
    "lh1_kalman_flight",
    "lh2_crossingBeam_jitter",
    "lh2_crossingBeam_move",
    "lh2_crossingBeam_flight",
    "lh2_kalman_jitter",
    "lh2_kalman_flight",
]


if __name__ == "__main__":

    for dataset in DATASETS:
        error = np.empty(0)
        total_duration = 0
        num_files = 0
        for file_usd in glob.glob("data/{}/log*".format(dataset)):
            data_usd = cfusdlog.decode(file_usd)
            assert(data_usd['activeMarkerModeChanged']['mode'][0] == 1)
            assert(data_usd['activeMarkerModeChanged']['mode'][1] == 0)
            cf_start_time = data_usd['activeMarkerModeChanged']['timestamp'][0]
            cf_end_time = data_usd['activeMarkerModeChanged']['timestamp'][1]
            cf_duration = cf_end_time - cf_start_time
            total_duration += cf_duration
            num_files += 1
        print("{} & {} & {:.0f}".format(dataset, num_files, total_duration/1000))

