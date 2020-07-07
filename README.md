# PySICKTiM - A Python Library for TCP communication with  the SICK TiM5xx series sensors

## Disclaimer
This library is a modification on the original PySICKTiM library made by Daniyal Ansari
(@ansarid). Major differences:
* This version uses TCP instead of USB for communication
* This version is compatible with python3.7


Introduction
------

This is a python library made to interact with the SICK TiM561 LiDAR sensor over the USB connection. This library was created to help developers who are using python to implement the TiM5xx LiDAR easily into their projects using python.

 The functions of this library includes:
 * Reading Settings and Data
 * Configuring Settings
 * Error Handling. 

The functions in this library are based off the [TiM5xx Series LiDAR](https://cdn.sick.com/media/docs/7/27/927/Technical_information_Telegram_Listing_Ranging_sensors_LMS1xx_LMS5xx_TiM5xx_MRS1000_MRS6000_NAV310_LD_OEM15xx_LD_LRS36xx_LMS4000_en_IM0045927.PDF) telegram documentation.
File included in pysicktim/references.

See [Examples](pysicktim/examples) for usage instructions.

Prerequisites
------
* easydict
* numpy
* pygame (Only for visualization)
```    
pip install -r requirements.txt
```
Installation
------

from source:

    git clone <url>
    cd pysicktim
    sudo pip3 install -r requirements.txt
    sudo python3 setup.py install
