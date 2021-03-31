# -*- coding: utf-8 -*-
"""
plotting the Euclidean error in 3D
"""
import matplotlib.pyplot as plt
import argparse
import numpy as np
import glob
from rigid_transform import compute_rigid_transform
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from temporal_alignment import TemporalAlignment

DATASETS = [
    "lh1_crossingBeam_move",
    "lh1_crossingBeam_flight",
    "lh1_kalman_flight",
    "lh2_crossingBeam_move",
    "lh2_crossingBeam_flight",
    "lh2_kalman_flight",
]


if __name__ == "__main__":

    errors = []
    for dataset in DATASETS:
        error = np.empty(0)
        for file_usd in glob.glob("data/{}/log*".format(dataset)):
            print("Analyzing {}".format(file_usd))
            file_mocap = file_usd.replace("log", "mocap") + ".npy"
            r = TemporalAlignment(file_usd, file_mocap)
            error = np.append(error, r.error)
        errors.append(error)

    fig1, ax1 = plt.subplots()
    ax1.boxplot(errors)
    ax1.set_xticklabels(DATASETS)
    ax1.set_ylabel("Euclidean Error [m]")
    plt.show()
