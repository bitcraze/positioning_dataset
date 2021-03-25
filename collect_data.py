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
import os
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
INTENSITY = 100
usdCanLog = None

def consoleReceived(data):
    print(data, end='')


def paramReceived(name, value):
    global usdCanLog
    if name == "usd.canLog":
        usdCanLog = int(value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file_mocap')
    parser.add_argument('estimation_mode', choices=['crossingBeam', 'kalman'])
    parser.add_argument('operation_mode', choices=['time', 'flightSweep', 'flightRandom'])
    parser.add_argument('--time', default=10, type=int)
    parser.add_argument('--velocity', default=0.5, type=float)
    args = parser.parse_args()

    # Only output errors from the logging framework
    logging.basicConfig(level=logging.ERROR)

    # Create output folder, if needed
    folder = os.path.dirname(args.file_mocap)
    os.makedirs(folder, exist_ok=True)

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

        if usdCanLog != 1:
            exit("Can't log to USD!")


        if args.estimation_mode == 'crossingBeam':
            # enable lighthouse crossing beam method
            cf.param.set_value('lighthouse.method', 0)
        elif args.estimation_mode == 'kalman':
            cf.param.set_value('lighthouse.method', 1)
        else:
            exit("Unknown mode", args.estimation_mode)

        # start logging motion capture data
        qtmThread = QtmThread(None, args.file_mocap)

        # start logging in uSD card
        cf.param.set_value('usd.logging', 1)
        time.sleep(2)

        # enable active marker deck
        cf.param.set_value('activeMarker.mode', 1)
        time.sleep(2)

        size = np.array([1.5,1.5,1.5])
        offset = np.array([-1.2,-0.9,0.25])
        delta = 0.5

        x_min = offset[0]
        x_max = offset[0] + size[0]
        y_min = offset[1]
        y_max = offset[1] + size[1]
        z_min = offset[2]
        z_max = offset[2] + size[2]

        if args.operation_mode == 'flightSweep':
            with PositionHlCommander(scf,default_velocity=args.velocity) as pc:
                for z in np.arange(z_min, z_max, delta):
                    # sweeping pattern
                    for y in np.arange(y_min, y_max, 2*delta):
                        pc.go_to(x_min, y, z)
                        pc.go_to(x_max, y, z)
                        pc.go_to(x_max, y+delta, z)
                        pc.go_to(x_min, y+delta, z)

                pc.go_to(0, 0, 0.05)
        elif args.operation_mode == 'flightRandom':
            with PositionHlCommander(scf,default_velocity=args.velocity) as pc:
                start = time.time()
                while time.time() - start < args.time:
                    pos = np.random.uniform(offset, offset+size)
                    pc.go_to(pos[0], pos[1], pos[2])
                pc.go_to(0, 0, 0.05)
        elif args.operation_mode == 'time':
            time.sleep(args.time)
        else:
            exit("unknown operation_mode", args.operation_mode)

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
