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
    def __init__(self, host=None):
        Thread.__init__(self)

        self.host = host
        # self.on_pose = None
        # self.connection = None
        # self.qtm_6DoF_labels = []
        self._stay_open = True

        self.start()

    def close(self):
        self._stay_open = False
        self.join()

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
            components=['3dnolabels'],
            on_packet=self._on_packet)

    async def _discover(self):
        async for qtm_instance in qtm.Discover('0.0.0.0'):
            return qtm_instance

    def _on_packet(self, packet):
        # print("Framenumber: {}".format(packet.framenumber))
        # print(packet.timestamp)
        header, markers = packet.get_3d_markers_no_label()
        # header, markers = packet.get_3d_markers()
        # print("Component info: {}".format(header))
        # for marker in markers:
            # print("\t", marker)
        if len(markers) == 4:
            print(packet.timestamp)
            a = np.empty((4,3))
            for i, marker in enumerate(markers):
                a[i] = [marker.x, marker.y, marker.z]
            a /= 1000
            pos = np.mean(a, axis=0)
            print(pos)
        else:
            print("Warning!", len(markers))

    async def _close(self):
        await self.connection.stream_frames_stop()
        self.connection.disconnect()


# Connect to QTM
qtm_wrapper = QtmThread(None)#"192.168.5.21")
time.sleep(10)
qtm_wrapper.close()
