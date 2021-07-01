## **Introduction**

COPIS represents a generic hardware/software framework for multi-view 360 degree imaging. SZRC is the firmware that runs on each COPIS controller. Command parsing and motion control within SZRC was originally derived from grbl v0.8c, but streamlined to remove extraneous functionality and extended to control “point and shoot”, DSLRs and mirrorless cameras, support camera pan & tilt positioning, and enable multi-controller operations utilizing UART and TWI serial protocols.

## **Command Set**

**Multi-controller communications**
* *Pass [CMD] onto the target controller [DeviceID] via TWI*
  * Command: >
  * Format: >[DeviceID][CMD]
  * Examples: >1G0X100
  * Notes: If omitted, command will be executed by master controller. [CMD] sent to target device.
* *Request data from target controller via TWI*
  * Not yet implemented
  * Command: <
  * Format: <[DeviceID]*[DataType]
  * Examples: <1*0
  * Data Types Definitions:
  * 0 -> System Data (current state & position)
  * 1 -> Settings Data (list of settings)

**Remote Shutter Control**
* *Press Shutter for P milliseconds or S seconds*
  * Command: C0
  * Format: C0[P/S][TIME]
* *Press Auto Focus  for P milliseconds or S seconds*
  * Command: C1
  * Format: C1[P/S][TIME]

**Positioning Modes**
* *Set absolute distance mode for target device (default)*
  * Command: G90
* *Set relative distance mode for target device*
  * Command: G91

**Positioning Cameras**
* *Rapid positioning at Max Feed Rate for each axis*
  * Command: G0
  * Format:	G0X[##]Y[##]Z[##]P[##]T[##]
  * Examples: G0X100Y50T25
* *Linear movement at feed rate (F) in distance mm/minute*
  * Command: G1
  * Format:	G1X[##]Y[##]Z[##]P[##]T[##]F[##]
  * Examples: G1X100Y50T25F900
  
**Calibrating Position**
* *Home one or more axes on the target controller, moving them towards their endstops until triggered*
  * Command: G28
  * Format: G28X[##]Y[##]Z[##]P[##]T[##]F[##]
  * Example: G28XZPT
  * Notes: G28 without parameters auto-homes all axes. Any distances defined by axis will determine direction and max distance to scan for homing. Generally these should be left out unless a given setup requires overriding defaults. A Feed rate may be provided to alter speed of homing. 
* *Define a home offset*
  * Command: M428X[##]Y[##]Z[##]P[##]T[##]
  * Notes: Sets current position to zero and defines a persistent offset from previous zero position (ie home). During homing - once limit is found, a move defined by the offset is made and zero reset.  
* *Set Position of one or more axis*
  * Command: G92X[##]Y[##]Z[##]P[##]T[##]
  * Notes: Can be called after homing to define what known position other than 0, for the home position. Client config should store home coordinates for each axis (determined during machine setup) and set after homing.  

**Device Configuration**
* *Define Device ID*
  * Command: M101
  * Format:	M101V[#]
  * Examples: M101V2
* *Set max travel distance*
  * Command: M208
  * Format:	M208X[##]Y[##]Z[##]P[##]T[##]
  * Examples: M208Y1000
* *Set min travel distance*
  * Command: M209
  * Format:	M209X[##]Y[##]Z[##]P[##]T[##]
  * Examples: M209Y-1000
* *Reset settings to defaults*
  * Command: M502
* *Print settings to UART*
  * Command: M503
  * Notes: Can be sent via TWI, but currently only displays to direct serial for each controller
  
**Other Commands**
* *Pause device for P milliseconds or S seconds*
  * Command: G4
  * Format: G4[P/S][TIME]
