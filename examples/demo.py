### Example script for working with the lidar
from pprint import pprint

import pysicktim.pysicktim.pysicktim as pysicktim
from easydict import EasyDict as edict
import logging

logging.basicConfig(level=logging.DEBUG)

# creating a lidar object
lidar = pysicktim.LiDAR()

# device can be given a name during initialization, call lidar.readLocationName() to retrieve
lidar = pysicktim.LiDAR(name="testlidar")

# user access credentials can be supplied during object initialisation.
# Default credentials can be found in the source code of setaccessmode
lidar = pysicktim.LiDAR(name="testlidar", user="03",password="F4724744")

# open lidar TCP socket connection before sending commands
lidar.open()
# commands can be send directly using send. See the telegram listing specification. No need to add start and stop bytes.
# At the moment only ASCII is supported
lidar.send("sRN SCdevicestate")
# Read the response from the device. Make sure there is a response expected.
# Socket timeout can be set during object initialisation, default is none
msg = lidar.read()
print(msg)

# Wrapper functions expand on the default telegram listing functions with parsing and error handling when appropriate.
# socket needs to be open, but lidar.read() is called automatically
print(lidar.firmwarev())
print("Device state: " + lidar.devicestate())

# Scan polls the device and returns a dict with scan information.
# scan.distances contains all parsed distances.
# Combine with scan.dist_start_angle and scan.dist_res for complete information.
scan = lidar.scan()
pprint(scan)

# Close lidar after operations are finished
lidar.close()

