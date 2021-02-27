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

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.utils.power_switch import PowerSwitch
from cflib.positioning.position_hl_commander import PositionHlCommander

URI = 'radio://0/60/2M/E7E7E7E7E7'
INTENSITY = 50

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    s = PowerSwitch(URI)
    s.stm_power_cycle()
    s.close()
    time.sleep(5)

    lg = LogConfig(name='Battery', period_in_ms=10)
    lg.add_variable('pm.vbat', 'float')
    lg.add_variable('lighthouse.status', 'uint8_t')

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf

        # enable active marker deck
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

        # enable lighthouse crossing beam method
        cf.param.set_value('lighthouse.method', 0)

        # start logging in uSD card
        cf.param.set_value('usd.logging', 1)
        time.sleep(2)

        # auto-flicking
        cf.param.set_value('health.startFlick', 1)
        time.sleep(1)

        with PositionHlCommander(scf,default_velocity=0.25) as pc:
            pc.forward(1.0)
            # pc.left(1.0)
            pc.back(1.0)
            # pc.go_to(0.0, 0.0, 1.0)


        # stop logging in uSD card
        cf.param.set_value('usd.logging', 0)
        time.sleep(1)