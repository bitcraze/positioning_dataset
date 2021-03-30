# -*- coding: utf-8 -*-
#
# ,---------,       ____  _ __
# |  ,-^-,  |      / __ )(_) /_______________ _____  ___
# | (  O  ) |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
# | / ,--'  |    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#    +------`   /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
# Copyright (C) 2019 Bitcraze AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, in version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Test script for QTM
"""
import asyncio
import math
import time
from threading import Thread
import numpy as np

import qtm


class QtmThread(Thread):
    def __init__(self, host=None, filename='mocap.npy'):
        Thread.__init__(self)

        self.host = host
        # self.on_pose = None
        # self.connection = None
        # self.qtm_6DoF_labels = []
        self._stay_open = True
        self._start_time = None
        self._end_time = None
        self._data = []
        self._filename = filename
        self._framenumber = None
        self._totalFrames = 0
        self._invalidFrames = 0
        # self._f = open(filename, "w")
        # self._f.write("time[ms],x[m],y[m],z[m]\n")

        self.start()

    def close(self):
        self._stay_open = False
        self.join()

        # compare camera time and wall-clock time
        wall_clock_duration = (self._end_time - self._start_time) * 1000
        data = np.array(self._data)
        camera_duration = data[-1,0] - data[0,0]
        print("Wall clock duration: {} ms; camera duration: {} ms; diff: {} ms".format(
            wall_clock_duration,
            camera_duration,
            wall_clock_duration - camera_duration))

        # write output file
        np.save(self._filename, data)

    def run(self):
        asyncio.run(self._life_cycle())

    async def _life_cycle(self):
        await self._connect()
        while(self._stay_open):
            await asyncio.sleep(1)
        await self._close()

    async def _connect(self):
        if self.host is None:
            qtm_instance = await self._discover()
            self.host = qtm_instance.host
        print('Connecting to QTM on ' + self.host)
        self.connection = await qtm.connect(self.host)

        await self.connection.stream_frames(
            components=['3dnolabels', '2d'],
            on_packet=self._on_packet)

    async def _discover(self):
        async for qtm_instance in qtm.Discover('0.0.0.0'):
            return qtm_instance

    def _on_packet(self, packet):
        if self._framenumber is not None and self._framenumber + 1 != packet.framenumber:
            print("Warning: Skipped a frame!", self._framenumber, packet.framenumber)
        self._framenumber = packet.framenumber
        self._totalFrames += 1
        # print("Framenumber: {}".format(packet.framenumber))
        # print(packet.timestamp)
        header, markers3d = packet.get_3d_markers_no_label()
        # header, markers = packet.get_3d_markers()
        # print("Component info: {}".format(header))
        # for marker in markers:
            # print("\t", marker)
        if len(markers3d) == 4:
            a = np.empty((4,3))
            for i, marker in enumerate(markers3d):
                a[i] = [marker.x, marker.y, marker.z]
            a /= 1000
            pos = np.mean(a, axis=0)
            self._data.append([packet.timestamp / 1000, 
                pos[0], pos[1], pos[2],
                a[0][0], a[0][1], a[0][2],
                a[1][0], a[1][1], a[1][2],
                a[2][0], a[2][1], a[2][2],
                a[3][0], a[3][1], a[3][2]])
            if self._start_time is None:
                self._start_time = time.time()
                self._totalFrames = 1
            self._end_time = time.time()
            # self._f.write("{},{},{},{}\n".format(packet.timestamp / 1000, pos[0], pos[1], pos[2]))
            # self._has_ever_received_markers = True
        else:
            _, markers2d = packet.get_2d_markers()
            num_markers2d = sum([len(m) for m in markers2d])
            if num_markers2d > 0:
                self._data.append([packet.timestamp / 1000, 
                    np.nan, np.nan, np.nan,
                    np.nan, np.nan, np.nan,
                    np.nan, np.nan, np.nan,
                    np.nan, np.nan, np.nan,
                    np.nan, np.nan, np.nan])
                if self._start_time is None:
                    self._start_time = time.time()
                    self._totalFrames = 1
                self._end_time = time.time()
                # self._f.write("{},{},{},{}\n".format(packet.timestamp / 1000, np.nan, np.nan, np.nan))
                # if self._has_ever_received_markers:
                self._invalidFrames += 1
                print("[{}] Warning: only {} markers visible! Missed {} %.".format(
                    time.time(),
                    len(markers3d),
                    self._invalidFrames/self._totalFrames*100.0))

    async def _close(self):
        await self.connection.stream_frames_stop()
        self.connection.disconnect()


if __name__ == '__main__':
    # Connect to QTM
    qtmThread = QtmThread(None)#"192.168.5.21")
    time.sleep(10)
    qtmThread.close()
