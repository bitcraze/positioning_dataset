# positioning_dataset

This repository contains scripts to collect and analyze data to quantify the accuracy and performance of different positioning systems. The goal is to quantify the difference of the various systems for different scenarios as well as identifying potential bugs.

## Lighthouse (vs Qualisys Motion Capture)

Here, we quantify the Lighthouse absolute accuracy as well as its jitter. We look at two different modes:

1. Crossing Beam Method. In this method only the position is estimated and there are no underlying assumptions of the vehicle dynamics. This is a good approach to use as a baseline, for example when using the Lighthouse to quantify improvements of state estimators operating with the LPS.

2. Kalman filter. This method is used during regular flight, directly considers the sweeping angles and IMU sensor data, and fuses all the information in an Extended Kalman filter. The data collected here can quantify the expected flight accuracy and used to tune (or generally improve) the existing Kalman filter.

### Experimental Setup

#### Crazyflie

Crazyflie 2.1 with long header pins, uSD-card deck, Lighthouse deck, and active marker deck (from bottom to top). Note that if you put the Lighthouse deck above the active marker deck, there will be interference.

The firmware is currently in dev-datacollection, which is close to master with some additional event triggers.

#### Motion Capture

We use Optitrack at 300 Hz in 'passive active marker mode'.
TODO: add description on how to enable that.

We calibrate the system using the Qualisys calibration kit.

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

First, the initial alignment is determent by a physical event that can be observed from both (motion capture and Crazyflie) systems. Here, we turn the IR LEDs on the active marker deck on at the beginning and off at the end. On the Crazyflie side, we record a timestamp for each of the events. On the motion capture side, we record the camera timestamps when we first and last see the markers. The offset and relative scale of the two clocks can then be easily computed. Another physical event we explored was "flicking" the Crazyflie and observing the IMU data/sudden movement, but this yields a less accurate and reproducible result.

Second, we numerically refine this initial guess using an exhaustive search. For all possible relative start/end time offsets (in the range of -100 to +100ms), we compute the spatial alignment. We use the relative start/end time offset that yielded the lowest residual error.

#### Error Metrics

Jitter of n positions: sqrt(1/n * sum_i=2^n ||position_i - position_{i-1}||^2)

Absolute Euclidean error: ||position_mocap - position_lh|| (we report mean and worst case values)

### Results

TODO: where to but raw data files?

#### LH1 Crossing Beam, Jitter

#### LH1 Crossing Beam, Manual Movement

#### LH1 Crossing Beam, Flight

#### LH1 Kalman, Flight

#### LH2 Crossing Beam, Jitter

#### LH2 Crossing Beam, Manual Movement

#### LH2 Crossing Beam, Flight

#### LH2 Kalman, Flight

