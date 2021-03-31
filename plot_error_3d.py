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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()

    error = np.empty(0)
    pos = np.empty((0, 3))
    for file_usd in glob.glob(args.folder + "/log02"):
        print("Analyzing {}".format(file_usd))
        file_mocap = file_usd.replace("log", "mocap") + ".npy"
        r = TemporalAlignment(file_usd, file_mocap)
        error = np.append(error, r.error)
        pos = np.append(pos, r.pos_mocap_merged[r.valid], axis=0)

    fig1, ax1 = plt.subplots()
    # ax1.set_title('Basic Plot')
    ax1.boxplot(error)
    plt.show()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    p3d = ax.scatter(pos[:,0], pos[:,1], pos[:,2], s=30, c=error, cmap=cm.coolwarm)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    fig.colorbar(p3d, label='Euclidean Error [m]')
    plt.show()
