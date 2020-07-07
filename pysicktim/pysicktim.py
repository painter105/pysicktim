# import usb.core
# import usb.util
import socket
import time
import unicodedata
import struct
import ctypes
import logging
from easydict import EasyDict as edict

log = logging.getLogger(__name__)


BUFFER_SIZE = 65535 # From original PySICKTiM


################################################################
#   ERRORS

class InvalidData(Exception):
    pass

class LidarNotFound(Exception):
    pass

class LidarException(Exception):
    """"Exception thrown by the device with specific error code and description"""

    def __init__(self,error_code,description):
        self.error_code = error_code
        self.description = description

        super().__init__(f"{error_code} : {description}")

error_codes=[
    "Sopas_Ok",
    "Sopas_Error_METHODIN_ACCESSDENIED",
    "Sopas_Error_METHODIN_UNKNOWNINDEX",
    "Sopas_Error_VARIABLE_UNKNOWNINDEX",
    "Sopas_Error_LOCALCONDITIONFAILED",
    "Sopas_Error_INVALID_DATA",
    "Sopas_Error_UNKNOWN_ERROR",
    "Sopas_Error_BUFFER_OVERFLOW",
    "Sopas_Error_BUFFER_UNDERFLOW",
    "Sopas_Error_ERROR_UNKNOWN_TYPE",
    "Sopas_Error_VARIABLE_WRITE_ACCESSDENIED",
    "Sopas_Error_UNKNOWN_CMD_FOR_NAMESERVER",
    "Sopas_Error_UNKNOWN_COLA_COMMAND",
    "Sopas_Error_METHODIN_SERVER_BUSY",
    "Sopas_Error_FLEX_OUT_OF_BOUNDS",
    "Sopas_Error_EVENTREG_UNKNOWNINDEX",
    "Sopas_Error_COLA_A_VALUE_OVERFLOW",
    "Sopas_Error_COLA_A_INVALID_CHARACTER",
    "Sopas_Error_OSAI_NO_MESSAGE",
    "Sopas_Error_OSAI_NO_ANSWER_MESSAGE",
    "Sopas_Error_INTERNAL",
    "Sopas_Error_HubAddressCorrupted",
    "Sopas_Error_HubAddressDecoding",
    "Sopas_Error_HubAddressAddressExceeded",
    "Sopas_Error_HubAddressBlankExpected",
    "Sopas_Error_AsyncMethodsAreSuppressed",
    "Sopas_Error_ComplexArraysNotSupported"
    ]


error_descriptions = {
    "Sopas_Error_METHODIN_ACCESSDENIED": "Wrong userlevel, access to method not allowed",
    "Sopas_Error_METHODIN_UNKNOWNINDEX": "Trying to access a method with an unknown Sopas index",
    "Sopas_Error_scandatacfgVARIABLE_UNKNOWNINDEX": "Trying to access a variable with an unknown Sopas index",
    "Sopas_Error_LOCALCONDITIONFAILED": "Local condition violated, e.g. giving a value that exceeds the minimum or maximum allowed value for this variable",
    "Sopas_Error_INVALID_DATA": "Invalid data given for variable, this errorcode is deprecated (is not used anymore).",
    "Sopas_Error_UNKNOWN_ERROR": "An error with unknown reason occurred, this errorcode is deprecated.",
    "Sopas_Error_BUFFER_OVERFLOW": "The communication buffer was too small for the amount of data that should be serialised.",
    "Sopas_Error_BUFFER_UNDERFLOW": "More data was expected, the allocated buffer could not be filled.",
    "Sopas_Error_ERROR_UNKNOWN_TYPE": "The variable that shall be serialised has an unknown type. This can only happen when there are variables in the firmware of the device that do not exist in the released description of the device. This should never happen.",
    "Sopas_Error_VARIABLE_WRITE_ACCESSDENIED": "It is not allowed to write values to this variable. Probably the variable is defined as read-only.",
    "Sopas_Error_UNKNOWN_CMD_FOR_NAMESERVER": "When using names instead of indices, a command was issued that the nameserver does not understand.",
    "Sopas_Error_UNKNOWN_COLA_COMMAND": "The CoLa protocol specification does not define the given command, command is unknown.",
    "Sopas_Error_METHODIN_SERVER_BUSY": "It is not possible to issue more than one command at a time to an SRT device.",
    "Sopas_Error_FLEX_OUT_OF_BOUNDS": "An dataay was accessed over its maximum length.",
    "Sopas_Error_EVENTREG_UNKNOWNINDEX": "The event you wanted to register for does not exist, the index is unknown.",
    "Sopas_Error_COLA_A_VALUE_OVERFLOW": "The value does not fit into the value field, it is too large.",
    "Sopas_Error_COLA_A_INVALID_CHARACTER": "Character is unknown, probably not alphanumeric.",
    "Sopas_Error_OSAI_NO_MESSAGE": "Only when using SRTOS in the firmware and distributed variables this error can occur. It is an indication that no operating system message could be created. This happens when trying to GET a variable.",
    "Sopas_Error_OSAI_NO_ANSWER_MESSAGE": "This is the same as \"Sopas_Error_OSAI_NO_MESSAGE\" with the difference that it is thrown when trying to PUT a variable.",
    "Sopas_Error_INTERNAL": "Internal error in the firmware, problably a pointer to a parameter was null.",
    "Sopas_Error_HubAddressCorrupted": "The Sopas Hubaddress is either too short or too long.",
    "Sopas_Error_HubAddressDecoding": "The Sopas Hubaddress is invalid, it can not be decoded (Syntax).",
    "Sopas_Error_HubAddressAddressExceeded": "Too many hubs in the address",
    "Sopas_Error_HubAddressBlankExpected": "When parsing a HubAddress an expected blank was not found. The HubAddress is not valid.",
    "Sopas_Error_AsyncMethodsAreSuppressed": "An asynchronous method call was made although the device was built with \“AsyncMethodsSuppressed\”. This is an internal error that should never happen in a released device.",
    "Sopas_Error_ComplexArraysNotSupported": "Device was built with „ComplexArraysSuppressed“ because the compiler does not allow recursions. But now a complex dataay was found. This is an internal error that should never happen in a released device."
    }

def remove_control_characters(s):
    s = "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
    return s

def dec_to_ascii(s):
    s = "".join(chr(x) for x in s)
    return s

def hex_to_dec(i):
    i = [ int(x,16) for x in i ]
    return i


def hex_to_meters(i):
    i = [ int(x,16)/1000 for x in i ]
    return i

def uint32(i):
    i = struct.unpack('>i', bytes.fromhex(i))[0]
    return i

def check_error(s):
    if s[0:3] == "sFA":
        error_code = error_codes[int(s[-1],16)]
        error_description = error_descriptions[error_code]
        raise LidarException(error_code,error_description)
        # return [error_code,error_description]
    else:
        return s

def parse_str(d):
    if d == None:
        return d
    else:
        d = d.split()
        d = d[len(d)-1]
        return d

## LIDAR FUNCTIONS ##

class LiDAR:

    tcp_ip = None
    tcp_port = None
    lidar = None
    connected = False
    socket_timeout = None

    def __init__(self,tcp_ip='169.254.219.5',tcp_port=2111,name=None,user=None,password=None,socket_timeout=None):
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.socket_timeout = socket_timeout

        self.open()
        if user is not None and password is not None:
            self.setaccessmode(user=user,password=password)
        elif user is None and password is None:
            pass
        elif user is None or password is None:
            raise Exception("Both user and password need to be provided.")


        if name is not None:
            if user is None or password is None:
                log.info("""
                Device name given but no access level credentials are provided.
                Defaulting to Authorized client credentials""")
                self.setaccessmode()

            self.setLocationName(name)

        log.debug("Succesfully ceated LiDAR object")
        log.debug(self.info())

        self.close()



    def info(self):
        """
        Returns information over the device
        :return: string
        """
        device_loc_name = self.readLocationName()
        device_ident = self.deviceident()
        device_type = self.devicetype()
        device_state = self.devicestate()

        return f"""
        Device Location Name = {device_loc_name}
        Device Type = {device_type}
        Device Identification Info: = {device_ident}
        Device State = {device_state}
        """

    def open(self):
        """
        Opens socket connection with the lidar.
        Remember to close the connection when the lidar is not needed anymore.
        :return: void
        """
        if not self.connected:
            self.lidar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self.socket_timeout is not None:
                self.lidar.settimeout(self.socket_timeout)

            self.lidar.connect((self.tcp_ip, self.tcp_port))
            self.connected = True

    def close(self):
        """
        Closes socket connection.
        :return: void
        """
        if self.connected:
            self.lidar.close()
            self.connected = False


    def read(self):
        """
        Reads response from lidar and returns parsed string checked for errors
        :return: string
        """
        if self.connected:
            msg = self.lidar.recv(BUFFER_SIZE)
            assert msg[:1] == b"\x02" and msg[-1:] == b"\x03", "improper open and close bytes in message"
            msg = check_error(msg)
            return msg[1:-1].decode("utf-8")

        else:
            raise LidarNotFound("LiDAR Device is not connected!")


    def send(self, cmd : str):
        """
        Sends a command directly to the lidar.

        See https://cdn.sick.com/media/docs/7/27/927/Technical_information_Telegram_Listing_Ranging_sensors_LMS1xx_LMS5xx_TiM5xx_TiM7xx_LMS1000_MRS1000_MRS6000_NAV310_LD_OEM15xx_LD_LRS36xx_LMS4000_en_IM0045927.PDF
            for commmands
        Opening and closing bytes are added automatically.
        :param cmd: string command without opening and closing bytes
        :return: success boolean
        """
        cmd = bytes(cmd,"utf-8")

        if self.connected:
            self.lidar.send(b"\x02"+cmd+b"\x03\0")
            return True
        else:
            log.error("LIDAR Device not found! Did you open the socket connection?")
            return self.connected

    #####################################################################
    #   Wrappers telegram functions as described in the telegram listing document. See this document for documentation.
    #   The functions can also be called directly using send()

    def firmwarev(self):
        self.send('sRN FirmwareVersion')
        answer = self.read()
        answer = answer.split()
        answer = answer[-1]
        return answer

    def deviceident(self):
        self.send('sRI0')
        answer = self.read()
        answer = answer.split()
        answer = answer[3] + ' ' + answer[4] + ' ' + answer[5]
        return answer

    def setaccessmode(self, user="03",password="F4724744"):
        # Userlevels:
        #   Maintenance: 02
        #   Authorized client: 03
        #   Service: 04
        # Passwords:
        #   Maintenance: B21ACE26
        #   Authorized client: F4724744
        #   Service: 81BE23AA

        self.send('sMN SetAccessMode '+user+" "+password)
        answer = self.read()
        if answer == "sAN SetAccessMode 1":
            return 0
        else:
            return answer

    def scancfg(self):   # Read for frequency and angular resolution
        # Request Read Command
        # sRN LMPscancfg
        self.send('sRN LMPscancfg')
        answer = self.read()
        answer = answer.split()

        if len(answer) == 7:
            scan_freq = int(answer[2],16)/100
            sectors = int(answer[3],16)
            ang_res = int(answer[4],16)/10000   # Manual says uint_32?
            start_ang = int(answer[5],32)/10000
            stop_ang = int(answer[6],32)/10000
            return [scan_freq,sectors,ang_res,start_ang,stop_ang]

        else:
            return answer

    def startmeas(self):   # Start measurement
        # sMN LMCstartmeas
        self.send('sMN LMCstartmeas')
        answer = self.read()
        if answer == "sAN LMCstartmeas 0":
            return 0
        else:
            return answer
        #   Start the laser and (unless in Standby mode) the motor of the the device

    def stopmeas(self):   # Stop measurement
        # sMN LMCstopmeas
        self.send('sMN LMCstopmeas')
        answer = self.read()
        if answer == "sAN LMCstopmeas 0":
            return 0
        else:
            return answer
        #   Shut off the laser and stop the motor of the the device

    def loadfacdef(self):   # Load factory defaults
        # sMN mSCloadfacdef
        self.send('sMN mSCloadfacdef')
        answer = self.read()
        if answer == "sAN mSCloadfacdef":
            return 0
        else:
            return answer

    def loadappdef(self):    # Load application defaults
        # sMN mSCloadappdef
        self.send('sMN mSCloadappdef')
        answer = self.read()
        return answer

    def checkpassword(self,user,password):    # Check password
        # sMN CheckPassword 03 19 20 E4 C9
        self.send('sMN CheckPassword '+user+' '+password)
        answer = self.read()
        return answer
        # sAN CheckPassword  1

    def reboot(self):    # Reboot device
        # sMN mSCreboot
        self.send('sMN mSCreboot')#
        answer = self.read()
        if answer == "sAN mSCreboot":
            return 0
        else:
            return answer
        # sAN mSCreboot

    def writeall(self):    # Save parameters permanently
        # sMN mEEwriteall
        self.send('sMN mEEwriteall')
        answer = self.read()
        return answer
        # sAN mEEwriteall 1

    def run(self):    # Set to run
        # sMN Run
        self.send('sMN Run')
        answer = self.read()
        if answer == "sAN Run 1":
            return 0
        else:
            return answer
        # sAN Run 1

    #####################################################################

    #   Measurement output telegram


    # # DOES NOT WORK YET
    # def scandatacfg(self, channel='01 00', rem_ang=1, res=1, unit=0, enc='00 00', pos=0, name=0, comment=0, time=0, out_rate='+1'):    # Configure the data content for the scan
    #     # sWN LMDscandatacfg 01 00 1 1 0 00 00 0 0 0 0 +1
    #     # sWN LMDscandatacfg 01 00 1 1 0 00 00 0  0 0 +10
    #     # sWN LMDscandatacfg 02 0 0 1 0 01 0 0 0 0 0 +10
    #     self.send('sWN LMDscandatacfg '+str(channel)+' '+str(rem_ang)+' '+str(res)+' '+str(unit)+' '+str(enc)+' '+str(pos)+' '+str(name)+' '+str(comment)+' '+str(time)+' '+str(out_rate))
    #     answer = self.read()
    #     if answer == "sWA LMDscandatacfg":
    #         return 0
    #     else:
    #         return answer
    #
    #     # sWA LMDscandatacfg

    def outputRange(self):    # Configure measurement angle of the scandata for output
        # sWN LMPoutputRange 1 1388 0 DBBA0
        self.send('sWN LMPoutputRange')
        answer = self.read()
        return answer
        # sWA LMPoutputRange

    def outputRange(self):    # Read for actual output range
        # sRN LMPoutputRange
        self.send('sRN LMPoutputRange')
        answer = self.read()
        return answer
        # sRA LMPoutputRange 1 1388 FFF92230 225510



    def scan(self, raw=False):    # Get LIDAR Data
        self.send('sRN LMDscandata')
        raw_data = self.read()
        data = raw_data

        scan = edict()

        if not raw:

            scan.dist_start = None
            scan.rssi_start = None

            log.debug(f"Scanresponse: {raw_data}")

            data = data.split()

            for index, item in enumerate(data):
                if "DIST" in item and scan.dist_start == None:
                    scan.dist_start = index

                if "RSSI" in item:
                    scan.rssi_start = index

            scan.telegram_len = len(data)
            scan.cmd_type = data[0]
            scan.cmd = data[1]
            scan.version = int(data[2], 16)
            scan.device_num = int(data[3], 16)
            scan.serial_num = int(data[4], 16)
            scan.device_stat = int(data[6], 8)
            scan.telegram_cnt = int(data[7], 16)
            scan.scan_cnt = int(data[8], 16)
            scan.uptime = int(data[9], 32)
            scan.trans_time = int(data[10], 32)
            # scan.input_stat =   int(str(data[11],data[12]),32)    # Takes both bytes into account
            scan.input_stat = int(data[12], 32)
            # scan.output_stat =  int(str(data[13],data[14]),8)     # Takes both bytes into account
            scan.output_stat = int(data[14], 8)
            scan.layer_ang = int(data[15], 16)
            scan.scan_freq = int(data[16], 32) / 100
            scan.meas_freq = int(data[17], 16) / 100  # Math may not be right
            scan.enc_amount = int(data[18], 16)

            scan.num_16bit_chan = int(data[19], 16)

            if scan.dist_start != None:

                scan.dist_label = data[20]
                scan.dist_scale_fact = int(data[scan.dist_start + 1], 16)
                scan.dist_scale_fact_offset = int(data[scan.dist_start + 2], 16)
                # scan.dist_start_ang = int(data[scan.dist_start + 3], 32) / 10000
                scan.dist_start_ang = (int(data[scan.dist_start + 3],16) - (1 << 32)) / 10000 # 32 bit unsigned int represented as hex
                scan.dist_angle_res = int(data[scan.dist_start + 4], 16) / 10000
                scan.dist_data_amnt = int(data[scan.dist_start + 5], 16)
                scan.dist_end = (scan.dist_start + 6) + scan.dist_data_amnt
                scan.distances = hex_to_meters(data[scan.dist_start + 6:scan.dist_end])
                scan.raw_distances = " ".join(data[scan.dist_start + 6:scan.dist_end])

            else:

                scan.dist_label = None
                scan.dist_scale_fact = None
                scan.dist_scale_fact_offset = None
                scan.dist_start_ang = None
                scan.dist_angle_res = None
                scan.dist_data_amnt = None
                scan.dist_end = None
                scan.distances = None
                scan.raw_distances = None

            if scan.rssi_start != None:

                scan.rssi_label = data[20]
                scan.rssi_scale_fact = int(data[scan.rssi_start + 1], 16)
                scan.rssi_scale_fact_offset = int(data[scan.rssi_start + 2], 16)
                scan.rssi_start_ang = (int(data[scan.dist_start + 3],16) - (1 << 32)) / 10000 # 32 bit unsigned int represented as hex
                scan.rssi_angle_res = int(data[scan.rssi_start + 4], 16) / 10000
                scan.rssi_data_amnt = int(data[scan.rssi_start + 5], 16)
                scan.rssi_end = (scan.rssi_start + 6) + scan.rssi_data_amnt
                scan.rssi = data[scan.rssi_start + 6:scan.rssi_end]

            else:

                scan.rssi_label = None
                scan.rssi_scale_fact = None
                scan.rssi_scale_fact_offset = None
                scan.rssi_start_ang = None
                scan.rssi_angle_res = None
                scan.rssi_data_amnt = None
                scan.rssi_end = None
                scan.rssi = None

            return scan
        else:
            return raw_data

    #####################################################################
    #   Filter

    def particle(self):    # Set particle filter
        # sWN LFPparticle 1 +500
        self.send('sWN LFPparticle')
        answer = self.read()
        return answer
        # sWA LFPparticle

    def meanfilter(self, status_code=0,number_of_scans="+10"):    # Set mean filter
        # sWN LFPmeanfilter 1 +10 0
        self.send('sWN LFPmeanfilter '+status_code+' '+number_of_scans+' 0')
        answer = self.read()
        return answer
        # sWA LFPmeanfilter


    #####################################################################
    #   Outputs



    def outputstate(self):    # Read state of the outputs
        # sRN LIDoutputstate
        self.send('sRN LIDoutputstate')
        answer = self.read()
        return answer

    def eventoutputstate(self, state):    # Send outputstate by event
        self.send('sEN LIDoutputstate '+str(state))
        answer = self.read()
        return answer

    def setoutput(self):    # Set output state
        # sMN mDOSetOutput 1 1
        self.send('sMN mDOSetOutput')
        answer = self.read()
        return answer
        # sAN mDOSetOutput 1
    #####################################################################
    #   Inputs

    def debtim(self):    # Set debouncing time for input x
        # sWN DI3DebTim +10
        self.send('sWN DI3DebTim')
        answer = self.read()
        return answer
        # sWA DI3DebTim

    def deviceident(self):    # Read device ident
        # sRN DeviceIdent
        self.send('sRN DeviceIdent')
        answer = self.read()
        answer = answer.split()
        answer = answer[3] + ' ' + answer[4] + ' ' + answer[5]
        return answer
        # sRA DeviceIdent 10 LMS10x_FieldEval 10 V1.36-21.10.2010

    def devicestate(self):    # Read device state
        # sRN SCdevicestate
        self.send('sRN SCdevicestate')
        answer = self.read()

        states = {
            0 : "Busy",
            1 : "Ready",
            2 : "Error",
            3 : "Standby"
        }
        return states[int(answer[-1])]
        # sRA SCdevicestate 0

    def ornr(self):    # Read device information
        # sRN DIornr
        self.send('sRN DIornr')
        answer = self.read()
        return answer
        # sRA DIornr 1071419

    def devicetype(self):    # Device type
        # sRN DItype
        self.send('sRN DItype')
        answer = self.read()
        return answer
        # sRA DItype E TIM561-2050101

    def oprh(self):    # Read operating hours
        # sRN ODoprh
        self.send('sRN ODoprh')
        answer = self.read()
        return answer
        # sRA ODoprh 2DC8B

    def pwrc(self):    # Read power on counter
        # sRN ODpwrc
        self.send('sRN ODpwrc')
        answer = self.read()
        return answer
        # sRA ODpwrc 752D

    def setLocationName(self, name):    # Set device name
        # sWN LocationName +13 OutdoorDevice
        name = " " + name
        string = 'sWN LocationName +'+str(len(name)-1)+name
        self.send(string)
        answer = self.read()
        return answer
        # sWA LocationName

    def readLocationName(self):    # Read for device name
        # sRN LocationName
        self.send('sRN LocationName')
        answer = self.read()
        answer = parse_str(answer)
        return answer
        # sRA LocationName D OutdoorDevice

    def rstoutpcnt(self):    # Reset output counter
        # sMN LIDrstoutpcnt
        self.send('sMN LIDrstoutpcnt')
        answer = self.read()
    #    answer = parse_str(answer)
        return answer
        # sAN LIDrstoutpcnt 0
