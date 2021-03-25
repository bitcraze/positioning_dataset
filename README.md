# positioning_dataset

This repository contains scripts to collect and analyze data to quantify the accuracy and performance of different positioning systems. The goal is to quantify the difference of the various systems for different scenarios as well as identifying potential bugs.

## Lighthouse (vs Qualisys Motion Capture)

Here, we quantify the Lighthouse absolute accuracy as well as its jitter. We look at two different modes:

1. Crossing Beam Method. In this method only the position is estimated and there are no underlying assumptions of the vehicle dynamics. This is a good approach to use as a baseline, for example when using the Lighthouse to quantify improvements of state estimators operating with the LPS.

2. Kalman filter. This method is used during regular flight, directly considers the sweeping angles and IMU sensor data, and fuses all the information in an Extended Kalman filter. The data collected here can quantify the expected flight accuracy and used to tune (or generally improve) the existing Kalman filter.

### Steps

1. Prepare Crazyflie 2.1
	1. add decks: long header pins, uSD-card deck, Lighthouse deck, and active marker deck (from bottom to top)
	2. Flash STM firmware (`dev-datacollection` branch)
	3. Put config.txt on uSD card deck
2. Prepare Motion Capture System
	1. Calibration (make sure to select in "Tools/Project Options/Input Devices/Cameras/Marker Mode/Type" the "Passive" option; place origin triangle on ground; walk around waving the wand)
	2. For tracking use the "untriggered active markers" mode (same menu as i.)
	3. Switch to 300 Hz Update rate
3. Prepare LightHouse
	1. Calibrate using cfclient (Origin and orientation of LH and Mocap do not have to match)
	2. Save the system config in the respective data folders
4. Collect Data
	1. Run scripts as outlined in the "Results" section
	2. Copy the resulting logXX files from the uSD card to the respective data folders
	3. Check collected data using the visualization/analysis scripts

### Experimental Setup

#### Crazyflie

Crazyflie 2.1 with long header pins, uSD-card deck, Lighthouse deck, and active marker deck (from bottom to top). Note that if you put the Lighthouse deck above the active marker deck, there will be interference.

The firmware is currently in the `dev-datacollection` branch, which is close to master with some additional event triggers.

#### Motion Capture

We calibrate the system using the Qualisys calibration kit. For calibration, make sure to select in "Tools/Project Options/Input Devices/Cameras/Marker Mode/Type" the "Passive" option.

We use Optitrack at 300 Hz in "untriggered active markers" mode.

#### Lighthouse

We calibrate the system using the CFclient. Note that the coordinate systems between motion capture and Lighthouse do not have to match, since we find the optimal transformation in postprocessing.

### Data Collection

The four major challenges were sensor interference, data storage, spatial alignment, and temporal alignment. For sensor interference, we found that using the active marker deck and disabling the IR strobe of the motion capture results in no measurable interference. For the data storage, we implemented and use the event-based logging system on uSD-card. For the remaining two, see the next subsection.

The data collection considers three different scenarios: 1) Jitter: move the Crazyflie to fixed locations and leave it stationary there; 2) Manual Movement: record data while the Crazyflie is mounted and moved on a stick (the stick is used to avoid occlusion caused by a human); and 3) record data while the Crazyflie is flying a preset trajectory within the area covered by Lighthouse.

### Analysis

Before analyzing the data, we need to align the two data streams (from motion capture and Crazyflie) both in space and time.

#### Spatial Alignment

If we assume that we have two temporally synchronized point clouds from two different, unknown coordinate systems, we can use the method described in

K. S. Arun, Thomas S. Huang, Steven D. Blostein:
Least-Squares Fitting of Two 3-D Point Sets. IEEE Trans. Pattern Anal. Mach. Intell. 9(5): 698-700 (1987)

to find the optimal transformation (translation and rotation) of the two coordinate systems. The assumption can be fulfilled by: 1) guessing some temporal alignment (offset and scaling); 2) pick one common time frame from one of the sensor sources (we use the data collected on-board the Crazyflie); 3) linearly interpolate the data of the second sensor source (here: motion capture data); 4) filtering points, where we did not have (valid) data from both sources. The output of the temporal alignment step is not only a transformation, but the residual error that remains when applying this transformation.

#### Temporal Alignment

The temporal alignment uses a two-step approach.

First, the initial alignment is determined by a physical event that can be observed from both (motion capture and Crazyflie) systems. Here, we turn the IR LEDs on the active marker deck on at the beginning and off at the end. On the Crazyflie side, we record a timestamp for each of the events. On the motion capture side, we record the camera timestamps when we first and last see the markers. The offset and relative scale of the two clocks can then be easily computed. Another physical event we explored was "flicking" the Crazyflie and observing the IMU data/sudden movement, but this yields a less accurate and reproducible result.

Second, we numerically refine this initial guess using an exhaustive search. For all possible relative start/end time offsets (in the range of -100 to +100ms), we compute the spatial alignment. We use the relative start/end time offset that yielded the lowest residual error.

#### Error Metrics

Jitter of n positions: sqrt(1/n * sum_i=2^n ||position_i - position_{i-1}||^2)

Absolute Euclidean error: ||position_mocap - position_lh|| (we report mean and worst case values)

### Results

All collected data is in the `data` subfolder.

#### LH1 Crossing Beam, Jitter

Repeat 5 times at different positions:

```
python3 collect_data.py data/lh1_crossingBeam_jitter/mocap00.npy crossingBeam time --time 10
```

#### LH1 Crossing Beam, Manual Movement

Mount CF on Stick and move it in random motions:
```
python3 collect_data.py data/lh1_crossingBeam_move/mocap00.npy crossingBeam time --time 120
```

#### LH1 Crossing Beam, Flight

```
python3 collect_data.py data/lh1_crossingBeam_flight/mocap00.npy crossingBeam flightSweep
```

00:
	x_min = -0.75
	x_max = 0.75
	y_min = -0.75
	y_max = 0.75
	z_min = 0.25
	z_max = 1.75
	delta = 0.5
	velocity = 0.5

01:
	velocity = 1.0

02:
	velocity = 0.25


```
python3 collect_data.py data/lh1_crossingBeam_flight/mocap03.npy crossingBeam flightRandom --time 120 --velocity 0.5
python3 collect_data.py data/lh1_crossingBeam_flight/mocap04.npy crossingBeam flightRandom --time 120 --velocity 0.25
python3 collect_data.py data/lh1_crossingBeam_flight/mocap05.npy crossingBeam flightRandom --time 120 --velocity 0.75
```

#### LH1 Kalman, Jitter

Repeat 5 times at different positions:

```
python3 collect_data.py data/lh1_kalman_jitter/mocap00.npy kalman time --time 10
```

#### LH1 Kalman, Flight

```
python3 collect_data.py data/lh1_kalman_flight/mocap00.npy kalman flightSweep --velocity 0.25
python3 collect_data.py data/lh1_kalman_flight/mocap01.npy kalman flightSweep --velocity 0.5
python3 collect_data.py data/lh1_kalman_flight/mocap02.npy kalman flightRandom --time 120 --velocity 0.25
python3 collect_data.py data/lh1_kalman_flight/mocap03.npy kalman flightRandom --time 120 --velocity 0.5
```

#### LH2 Crossing Beam, Jitter

Repeat 5 times at different positions:

```
python3 collect_data.py data/lh2_crossingBeam_jitter/mocap00.npy crossingBeam time --time 10
```

#### LH2 Crossing Beam, Manual Movement

Mount CF on Stick and move it in random motions:
```
python3 collect_data.py data/lh2_crossingBeam_move/mocap00.npy crossingBeam time --time 120
```

#### LH2 Crossing Beam, Flight

```
python3 collect_data.py data/lh2_crossingBeam_flight/mocap00.npy crossingBeam flightSweep --velocity 0.25
python3 collect_data.py data/lh2_crossingBeam_flight/mocap01.npy crossingBeam flightSweep --velocity 0.5
python3 collect_data.py data/lh2_crossingBeam_flight/mocap02.npy crossingBeam flightRandom --time 120 --velocity 0.25
python3 collect_data.py data/lh2_crossingBeam_flight/mocap03.npy crossingBeam flightRandom --time 120 --velocity 0.5
```

#### LH2 Kalman, Jitter

Repeat 5 times at different positions:

```
python3 collect_data.py data/lh2_kalman_jitter/mocap00.npy kalman time --time 10
```

#### LH2 Kalman, Flight

```
python3 collect_data.py data/lh2_kalman_flight/mocap00.npy kalman flightSweep --velocity 0.25
python3 collect_data.py data/lh2_kalman_flight/mocap01.npy kalman flightSweep --velocity 0.5
python3 collect_data.py data/lh2_kalman_flight/mocap02.npy kalman flightRandom --time 120 --velocity 0.25
python3 collect_data.py data/lh2_kalman_flight/mocap03.npy kalman flightRandom --time 120 --velocity 0.5
```

