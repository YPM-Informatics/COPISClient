## **Introduction**

COPIS represents a generic hardware/software framework for multi-view 360 degree imaging. SZRC is the firmware that runs on each COPIS controller. SZRC is derived from grbl v0.8c, but streamlined to remove extraneous functionality and extended to control “point and shoot”, DSLRs and mirrorless cameras, support camera pan & tilt positioning, and enable multi-controller communications utilizing UART and I2C serial protocols.

## **Command Codes**

**Multi-controller communications**		
* *Pass [CMD] onto to target controller [DeviceID] via I2C*
  * Command: >		
  * Format: >[DeviceID][CMD]
  * Examples: >1G0X100	
  * Notes: If omitted, command will be executed by master controller. [CMD} sent to traget device.
* *Request Data from target Controller via I2C*
  * Command: <
  * Format: <[DeviceID]*[DataType]
  * Examples: <1*0	
  * Data Types Definitions: 
  * 0 -> System Data (current state & position)
  * 1 -> Settings Data (list if settings)

**Positioning Cameras**			
* *Rapid positioning at Max Feed Rate for each Axis*
  * Command: G0	
  * Format:	G0X[##]Y[##]Z[##]P[##]T[##]
  * Examples: G1X100Y50T25	
* *Linear movement at feed rate (F) in distance mm/minute*
  * Command: G1
  * Format:	G1X[##]Y[##]Z[##]P[##]T[##]F[##]
  * Examples: G1X100Y50T25F900
* *Movement in an arc at specified feed rate (F)*
  * Commands: G2 & G3	
  * Notes: Not yet implemented	
* *Pause device for P milliseconds or S seconds*
  * Command: G4	
  * Format: G4[P/S][TIME]	
* *Select a plane for G2 & G3 arcs*
  * Commands: G17, G18 & G19
  * G17 -> XY plane
  * G18 -> ZX plane
  * G19 -> YZ plane	
  * Notes:	Not yet implemented	
* *Selecting Metric vs Imperial Measurement Systems*
  * Commands: G20 & G21
  * Notes: SZRC, at this time, works exclusively in metric; these commands are not supported.
* *Homing one or more axes on the target controller, moving them towards their endstops until triggered*
  * Command: G28[AXIS_LIST]
  * Example: G28XZPT
  * Notes: G28 without parameters auto-homes all axes. 
* *Set absolute distance mode for target device (default)*	
  * Command: G90		
* *Set relative distance mode for target device*
  * Command: G91		
* *Set Position of one or more axis*	
  * Command: G92		

**Remote Shutter Control**
* *Press Shutter for P milliseconds or S seconds*		
  * Command: C0
  * Format: C0[P/S][TIME]	
* *Press Auto Focus  for P milliseconds or S seconds*
  * Command: C1
  * Format: C1[P/S][TIME]

**USB PTP Camera Control**
* *Shutter Release*
  * In development
* *Auto Focus*
  * In development
* *Bulb Mode*
  * In development
* *Transfer Imgaery*
  * In development
* *Live View*
  * In development
  
**Other Commands**			
* *Pause/Resume Processing*
  * Pause Command: M0
  * Resume Command: M24	
  * Notes: M0 & M24 are used for syncing positions of cameras allowing the master or the PC to insert pauses until other commands complete. Also useful when EDSDK is being used from a PC to control camera therefore allowing the controller to wait until PC has finished downloading imagery (or some other process) before proceeding on to next action in the buffer. Alternatively, the PC could hold back on sending commands until transfer is finished, theby not needing to issue a Pause command.		
* *Enable All Motors*
  * Command: M17
  * Example: M17
* *Disable All Motors*
  * Command: M18
  * Example: M18
  

