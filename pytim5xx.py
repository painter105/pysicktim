import usb.core
import usb.util
import time
import unicodedata

'''
    Command basics
    ┌──────────────────┬────────────────┬────────────────────────────────┬────────────────────────────────┐
    │   Description    │ Value ASCII    │ Value Hex                      │ Value Binary                   │
    ├──────────────────┼────────────────┼────────────────────────────────┼────────────────────────────────┤
    │   Start of text  │ <STX>          │ 02                             │ 02 02 02 02 + given length     │
    ├──────────────────┼────────────────┼────────────────────────────────┼────────────────────────────────┤
    │   End of text    │ <ETX>          │ 03                             │ Calculated checksum            │
    ├──────────────────┼────────────────┼────────────────────────────────┴────────────────────────────────┤
    │   Read           │ sRN            │                             73 52 4E                            │
    ├──────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
    │   Write          │ sWN            │                             73 57 4E                            │
    ├──────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
    │   Method         │ sMN            │                             73 4D 4E                            │
    ├──────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
    │   Event          │ sEN            │                             73 45 4E                            │
    ├──────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
    │   Answer         │ sRA            │                             73 52 41                            │
    │                  │ sWA            │                             73 57 41                            │
    │                  │ sAN            │                             73 41 4E                            │
    │                  │ sEA            │                             73 45 41                            │
    │                  │ sSN            │                             73 53 4E                            │
    ├──────────────────┼────────────────┼────────────────────────────────┬────────────────────────────────┤
    │   Space          │ {SPC}          │ 20                             │ 20                             │
    └──────────────────┴────────────────┴────────────────────────────────┴────────────────────────────────┘
    If values are divided into two parts (e.g. measurement data), they are documented
    according to LSB 0 (e.g. 00 07), output however is according to MSB (e.g. 07 00).
'''
################################################################
#   ERRORS
#
# class Error(Exception):
#    """Base class for other exceptions"""
#    pass
#
# class Sopas_Error_METHODIN_ACCESSDENIED(Error):
#  """Wrong userlevel, access to method not allowed"""
#
# class Sopas_Error_METHODIN_UNKNOWNINDEX(Error):
#  """Trying to access a method with an unknown Sopas index"""
#
# class Sopas_Error_VARIABLE_UNKNOWNINDEX(Error):
#  """Trying to access a variable with an unknown Sopas index"""
#
# class Sopas_Error_LOCALCONDITIONFAILED(Error):
#  """Local condition violated, e.g. giving a value that exceeds the minimum or maximum allowed value for this variable"""
#
# class Sopas_Error_INVALID_DATA(Error):
#  """Invalid data given for variable, this errorcode is deprecated (is not used anymore)."""
#
# class Sopas_Error_UNKNOWN_ERROR(Error):
#  """An error with unknown reason occurred, this errorcode is deprecated."""
#
# class Sopas_Error_BUFFER_OVERFLOW(Error):
#  """The communication buffer was too small for the amount of data that should be serialised."""
#
# class Sopas_Error_BUFFER_UNDERFLOW(Error):
#  """More data was expected, the allocated buffer could not be filled."""
#
# class Sopas_Error_ERROR_UNKNOWN_TYPE(Error):
#  """The variable that shall be serialised has an unknown type. This can only happen when there are variables in the firmware of the device that do not exist in the released description of the device. This should never happen."""
#
# class Sopas_Error_VARIABLE_WRITE_ACCESSDENIED(Error):
#  """It is not allowed to write values to this variable. Probably the variable is defined as read-only."""
#
# class Sopas_Error_UNKNOWN_CMD_FOR_NAMESERVER(Error):
#  """When using names instead of indices, a command was issued that the nameserver does not understand."""
#
# class Sopas_Error_UNKNOWN_COLA_COMMAND(Error):
#  """The CoLa protocol specification does not define the given command, command is unknown."""
#
# class Sopas_Error_METHODIN_SERVER_BUSY(Error):
#  """It is not possible to issue more than one command at a time to an SRT device."""
#
# class Sopas_Error_FLEX_OUT_OF_BOUNDS(Error):
#  """An dataay was accessed over its maximum length."""
#
# class Sopas_Error_EVENTREG_UNKNOWNINDEX(Error):
#  """The event you wanted to register for does not exist, the index is unknown."""
#
# class Sopas_Error_COLA_A_VALUE_OVERFLOW(Error):
#  """The value does not fit into the value field, it is too large."""
#
# class Sopas_Error_COLA_A_INVALID_CHARACTER(Error):
#  """Character is unknown, probably not alphanumeric."""
#
# class Sopas_Error_OSAI_NO_MESSAGE(Error):
#  """Only when using SRTOS in the firmware and distributed variables this error can occur. It is an indication that no operating system message could be created. This happens when trying to GET a variable."""
#
# class Sopas_Error_OSAI_NO_ANSWER_MESSAGE(Error):
#  """This is the same as Sopas_Error_OSAI_NO_MESSAGE with the difference that it is thrown when trying to PUT a variable."""
#
# class Sopas_Error_INTERNAL(Error):
#  """Internal error in the firmware, problably a pointer to a parameter was null."""
#
# class Sopas_Error_HubAddressCorrupted(Error):
#  """The Sopas Hubaddress is either too short or too long."""
#
# class Sopas_Error_HubAddressDecoding(Error):
#  """The Sopas Hubaddress is invalid, it can not be decoded (Syntax)."""
#
# class Sopas_Error_HubAddressAddressExceeded(Error):
#  """Too many hubs in the address"""
#
# class Sopas_Error_HubAddressBlankExpected(Error):
#  """When parsing a HubAddress an expected blank was not found. The HubAddress is not valid."""
#
# class Sopas_Error_AsyncMethodsAreSuppressed(Error):
#  """An asynchronous method call was made although the device was built with “AsyncMethodsSuppressed”. This is an internal error that should never happen in a released device."""
#
# class Sopas_Error_ComplexArraysNotSupported(Error):
#  """Device was built with „ComplexArraysSuppressed“ because the compiler does not allow recursions. But now a complex dataay was found. This is an internal error that should never happen in a released device."""
#




timeout = 500
lidar = usb.core.find(idVendor=0x19a2, idProduct=0x5001)

if lidar is None:
    print('LIDAR Device not found!')
    exit()


############################################
#   Basic Settings

def remove_control_characters(s):
    s = "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
    return s

def dec_to_ascii(s):
    s = "".join(chr(x) for x in s)
    return s

def check_error(s):
    if s == "sFA 1":
        print("ERROR: ", s)
    else:
        pass

def parse_str(d):
    if d == None:
        return d
    else:
        d = d.split()
        d = d[len(d)-1]
        return d
## LIDAR FUNCTIONS ##

def read():
    arr = lidar.read(1|usb.ENDPOINT_IN,65535,timeout=100)
    return "".join([chr(x) for x in arr[1:-1]])

def send(cmd):
    print(cmd)
    lidar.write(2|usb.ENDPOINT_OUT,"\x02"+cmd+"\x03\0",0)
######################

def firmwarev():
    send('sRN FirmwareVersion')
    answer = read()
    return answer

def deviceident():
    send('sRI0')
    answer = read()
    return answer

def setaccessmode(user="03",password="F4724744"):
    send('sMN SetAccessMode '+user+" "+password)
    answer = read()
    return answer


def scancfg():   # Read for frequency and angular resolution
    # Request Read Command
    # sRN LMPscancfg
    send('sRN LMPscancfg')
    answer = read()
    return answer

def startmeas():   # Start measurement
    # sMN LMCstartmeas
    send('sMN LMCstartmeas')
    answer = read()
    return answer
    #   Start the laser and (unless in Standby mode) the motor of the the device

def stopmeas():   # Stop measurement
    # sMN LMCstopmeas
    send('sMN LMCstopmeas')
    answer = read()
    return answer

def loadfacdef():   # Load factory defaults
    # sMN mSCloadfacdef
    send('sMN mSCloadfacdef')
    answer = read()
    return answer
#   Shut off the laser and stop the motor of the the device

def loadappdef():    # Load application defaults
    # sMN mSCloadappdef
    send('sMN mSCloadappdef')
    answer = read()
    return answer

def CheckPassword(password):    # Check password
    # sMN CheckPassword 03 19 20 E4 C9
    send('sMN CheckPassword '+password)
    answer = read()
    return answer
    # sAN CheckPassword  1

def reboot():    # Reboot device
    # sMN mSCreboot
    send('sMN mSCreboot')#
    answer = read()
    return answer
    # sAN mSCreboot

def writeall():    # Save parameters permanently
    # sMN mEEwriteall
    send('sMN mEEwriteall')
    answer = read()
    return answer
    # sAN mEEwriteall 1

def run():    # Set to run
    # sMN Run
    send('sMN Run')
    answer = read()
    return answer
    # sAN Run 1
#####################################################################
#   Measurement output telegram

def scandatacfg():    # Configure the data content for the scan
    # sWN LMDscandatacfg 01 00 1 1 0 00 00 0 0 0 0 +1
    # sWN LMDscandatacfg 01 00 1 1 0 00 00 0  0 0 +10
    # sWN LMDscandatacfg 02 0 0 1 0 01 0 0 0 0 0 +10
    send('sWN LMDscandatacfg')
    answer = read()
    return answer
    # sWA LMDscandatacfg

def outputRange():    # Configure measurement angle of the scandata for output
    # sWN LMPoutputRange 1 1388 0 DBBA0
    send('sWN LMPoutputRange')
    answer = read()
    return answer
    # sWA LMPoutputRange

def outputRange():    # Read for actual output range
    # sRN LMPoutputRange
    send('sRN LMPoutputRange')
    answer = read()
    return answer
    # sRA LMPoutputRange 1 1388 FFF92230 225510

def scan(cont=False,cont_mode=0):    # Get LIDAR Data
    if cont == False:
        send('sRN LMDscandata')
        answer = read()
        return answer
    elif cont == True:
        send('sEN LMDscandata '+ str(cont_mode))  # Send Telegrams Continuously
# LMDscandata - reserved values PAGE 80

#####################################################################
#   Filter

def particle():    # Set particle filter
    # sWN LFPparticle 1 +500
    send('sWN LFPparticle')
    answer = read()
    return answer
    # sWA LFPparticle

def meanfilter(status_code=0,number_of_scans="+10"):    # Set mean filter
    # sWN LFPmeanfilter 1 +10 0
    send('sWN LFPmeanfilter '+status_code+' '+number_of_scans+' 0')
    answer = read()
    return answer
    # sWA LFPmeanfilter


#####################################################################
#   Outputs



def outputstate():    # Read state of the outputs
    # sRN LIDoutputstate
    send('sRN LIDoutputstate')

def eventoutputstate(state):    # Send outputstate by event
    send('sEN LIDoutputstate '+str(state))
    answer = read()
    return answer

def SetOutput():    # Set output state
    # sMN mDOSetOutput 1 1
    send('sMN mDOSetOutput')
    answer = read()
    return answer
    # sAN mDOSetOutput 1
#####################################################################
#   Inputs

def DebTim():    # Set debouncing time for input x
    # sWN DI3DebTim +10
    send('sWN DI3DebTim')
    answer = read()
    return answer
    # sWA DI3DebTim

def deviceident():    # Read device ident
    # sRN DeviceIdent
    send('sRN DeviceIdent')
    answer = read()
    return answer
    # sRA DeviceIdent 10 LMS10x_FieldEval 10 V1.36-21.10.2010

def devicestate():    # Read device state
    # sRN SCdevicestate
    send('sRN SCdevicestate')
    answer = read()
    return answer
    # sRA SCdevicestate 0

def ornr():    # Read device information
    # sRN DIornr
    send('sRN DIornr')
    answer = read()
    return answer
    # sRA DIornr 1071419

def devicetype():    # Device type
    # sRN DItype
    send('sRN DItype')
    answer = read()
    return answer
    # sRA DItype E TIM561-2050101

def oprh():    # Read operating hours
    # sRN ODoprh
    send('sRN ODoprh')
    answer = read()
    return answer
    # sRA ODoprh 2DC8B

def pwrc():    # Read power on counter
    # sRN ODpwrc
    send('sRN ODpwrc')
    answer = read()
    return answer
    # sRA ODpwrc 752D

def setLocationName(name):    # Set device name
    # sWN LocationName +13 OutdoorDevice
    name = " " + name
    string = 'sWN LocationName +'+str(len(name)-1)+name
    send(string)
    answer = read()
    return answer
    # sWA LocationName

def readLocationName():    # Read for device name
    # sRN LocationName
    send('sRN LocationName')
    answer = read()
    answer = parse_str(answer)
    return answer
    # sRA LocationName D OutdoorDevice

def rstoutpcnt():    # Reset output counter
    # sMN LIDrstoutpcnt
    send('sMN LIDrstoutpcnt')
    answer = read()
#    answer = parse_str(answer)
    return answer
    # sAN LIDrstoutpcnt 0