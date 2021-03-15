# -*- coding: utf-8 -*-
"""
plotting lh angles
"""
import cfusdlog
import matplotlib.pyplot as plt
import argparse
import numpy as np
import mplcursors

num_sensors = 4
num_lh = 2
num_sweeps = 2

def compute_measurement_id(sensor, basestation, sweep):
    return sensor * num_lh * num_sweeps + \
            basestation * num_sweeps + \
            sweep

# see https://stackoverflow.com/questions/22052532/matplotlib-python-clickable-points
def on_pick(event):
    print(event.ind)
    # artist = event.artist
    # xmouse, ymouse = event.mouseevent.xdata, event.mouseevent.ydata
    # x, y = artist.get_xdata(), artist.get_ydata()
    # ind = event.ind
    # print('Artist picked:', event.artist)
    # print('{} vertices picked'.format(len(ind)))
    # print('Pick between vertices {} and {}'.format(min(ind), max(ind)+1))
    # print('x, y of mouse: {:.2f},{:.2f}'.format(xmouse, ymouse))
    # print('Data point:', x[ind[0]], y[ind[0]])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_usd")
    args = parser.parse_args()

    # decode binary log data
    data_usd = cfusdlog.decode(args.file_usd)

    cf_start_time = 0 #data_usd['lhAngle']['timestamp'][0]

    # new figure
    fig, ax = plt.subplots(2,1,sharex=True)

    t = (np.array(data_usd['lhAngle']['timestamp']) - cf_start_time) / 1000
    d = compute_measurement_id(np.array(data_usd['lhAngle']['sensor']),
                                np.array(data_usd['lhAngle']['basestation']),
                                np.array(data_usd['lhAngle']['sweep']))
    ax[0].scatter(t, d)
    ax[0].set_ylabel('# Received LH Angle From ID')

    t = (np.array(data_usd['lhUartFrame']['timestamp']) - cf_start_time) / 1000
    d = compute_measurement_id(np.array(data_usd['lhUartFrame']['sensor']),
                                np.array(data_usd['lhUartFrame']['basestation']),
                                np.array(data_usd['lhUartFrame']['sweep']))
    ax[1].scatter(t, d, picker=10)
    ax[1].set_ylabel('# Received LH Angle From ID')

    ax[-1].set_xlabel('Time [s]')

    # fig.canvas.callbacks.connect('pick_event', on_pick)
    # mplcursors.cursor(hover=True)

    crs = mplcursors.cursor(ax[1],hover=True)

    crs.connect("add", lambda sel: sel.annotation.set_text(
        'Sensor {}\nBS {}\nSweep {}\nOffset {}\nTimestamp {}'.format(
            data_usd['lhUartFrame']['sensor'][sel.target.index],
            data_usd['lhUartFrame']['basestation'][sel.target.index],
            data_usd['lhUartFrame']['sweep'][sel.target.index],
            data_usd['lhUartFrame']['offset'][sel.target.index],
            data_usd['lhUartFrame']['timestampFPGA'][sel.target.index])))

    plt.show()

    # fig, ax = plt.subplots(16,1,sharex=True)
    # angles = np.array(data_usd['lhAngle']['angle'])
    # for sensor in range(num_sensors):
    #     for lh in range(num_lh):
    #         for sweep in range(num_sweeps):
    #             s = compute_measurement_id(sensor, lh, sweep)
    #             ax[s].plot(t[d==s], angles[d==s],'.-')
    #             ax[s].set_title("Sensor: {}, LH {}, Sweep: {}".format(sensor, lh, sweep))
    # plt.show()
