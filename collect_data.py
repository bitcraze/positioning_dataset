# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2019 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Example to use Qualisys active marker deck

Change the URI variable to your Crazyflie configuration.
"""
import logging
import time
import numpy as np
import argparse

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.utils.power_switch import PowerSwitch
from cflib.positioning.position_hl_commander import PositionHlCommander

from qtm_thread import QtmThread

URI = 'radio://0/60/2M/E7E7E7E7E7'
INTENSITY = 50
usdCanLog = False

def consoleReceived(data):
    print(data, end='')


def paramReceived(name, value):
    if name == "usd.canLog":
        usdCanLog = int(value)
    print(name, value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file_mocap")
    args = parser.parse_args()

    # Only output errors from the logging framework
    logging.basicConfig(level=logging.ERROR)

    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    s = PowerSwitch(URI)
    s.stm_power_cycle()
    s.close()
    time.sleep(5)

    lg = LogConfig(name='Battery', period_in_ms=10)
    lg.add_variable('pm.vbat', 'float')
    lg.add_variable('lighthouse.status', 'uint8_t')

    cf = cflib.crazyflie.Crazyflie()
    cf.console.receivedChar.add_callback(consoleReceived)

    with SyncCrazyflie(URI, cf) as scf:

        # check usd Deck
        cf.param.add_update_callback(group='usd', name='canLog', cb=paramReceived)
        cf.param.request_param_update('usd.canLog')

        # configure active marker deck
        cf.param.set_value('activeMarker.mode', 0)
        cf.param.set_value('activeMarker.front', INTENSITY)
        cf.param.set_value('activeMarker.back', INTENSITY)
        cf.param.set_value('activeMarker.left', INTENSITY)
        cf.param.set_value('activeMarker.right', INTENSITY)
        time.sleep(2)

        # check battery voltage
        with SyncLogger(scf, lg) as logger:
            for _, data, _ in logger:
                vbat = data['pm.vbat']
                lhStatus = data['lighthouse.status']
                break

        print("Battery voltage: {:.2f} V".format(vbat))
        print("LightHouse Status: {}".format(lhStatus))

        if vbat < 3.6:
            exit("Battery too low!")

        if lhStatus != 2:
            exit("LightHouse not working!")

        if usdCanLog != 0:
            exit("Can't log to USD!")


        # enable lighthouse crossing beam method
        cf.param.set_value('lighthouse.method', 0)

        # start logging motion capture data
        qtmThread = QtmThread(None, args.file_mocap)

        # start logging in uSD card
        cf.param.set_value('usd.logging', 1)
        time.sleep(2)

        # enable active marker deck
        cf.param.set_value('activeMarker.mode', 1)
        time.sleep(2)

        x_min = -0.5
        x_max = 1.0
        y_min = -1.5
        y_max = 0.0
        z_min = 0.25
        z_max = 0.3#1.0
        delta = 0.25

        with PositionHlCommander(scf,default_velocity=0.5) as pc:
            # sweeping pattern
            for y in np.arange(y_min, y_max, 2*delta):
                pc.go_to(x_min, y)
                pc.go_to(x_max, y)
                pc.go_to(x_max, y+delta)
                pc.go_to(x_min, y+delta)

        # time.sleep(60)

        # disable active marker deck
        cf.param.set_value('activeMarker.mode', 0)
        time.sleep(1)

        # stop logging in uSD card
        cf.param.set_value('usd.logging', 0)
        time.sleep(2)

        # stop mocap data collection
        qtmThread.close()

    # Turn CF off
    s = PowerSwitch(URI)
    s.stm_power_down()
    s.close()
