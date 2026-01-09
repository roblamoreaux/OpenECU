"""
 A ECU example of how to define a DUT driver.
"""
import sys
import opentap
from opentap import *
import clr
clr.AddReference("System.Collections")
import System
from System import String
from System.Collections.Generic import List
from OpenTap import Log, DisplayAttribute, Display, FilePathAttribute, FilePath
from System import Array, Double, Byte, Int32, String, Boolean # Import types to reference for generic methods
from System.ComponentModel import Browsable # BrowsableAttribute can be used to hide things from the user.
import System.Xml
from System.Xml.Serialization import XmlIgnore
from pya2l import DB
import pya2l.model as model
from pya2l import exceptions
from pya2l.a2l_listener import A2LListener
from pya2l.api.inspect import CompuMethod
from pya2l.api.inspect import Group
from pya2l.api.inspect import Measurement
from pya2l.api.inspect import Characteristic
from pya2l.api.inspect import ModCommon
from pya2l.api.inspect import ModPar
from pya2l.api.inspect import NoCompuMethod
from pya2l.api.inspect import TypedefStructure
from pya2l.parserlib import ParserWrapper
#CCP stuff imported here
from collections import namedtuple
import enum
import time
from pprint import pprint
import struct
import can
from can.bus import BusState
from can import *

from pythonccp import ccp
#from pythonccp.logger import Logger


MTA0 = 0
MTA1 = 1

#db = DB()

@attribute(OpenTap.Display("CAN DUT", "An CAN DUT driver.", "CAN DUTs"))
class CANDut(Dut):
    # Add a Firmware version setting which can be configured by the user.
    Firmware = property(String, "0.1.0")\
        .add_attribute(OpenTap.Display( "Firmware Version", "The firmware version of the DUT.", "Common"))
    """
    create fields for 
        selecting A2L file
        selecting CAN interface and parameters (use list)
        Selecing DTO
        Selecting CRO
        other stuff
    """
    #A2LFilePath = property(String, "c:\\OpenTAP\\LaforgeTestApp_CCU_tool_generic")\
    #    .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Open, ".A2L"))\
    #    .add_attribute(Display("A2L File Path", "File path for ECU Definition.", "ECU Definition"))
    #CRO = property(Int32, 0x6f9)\
    #    .add_attribute(Display("CRO to use", "CRO ID to use for commands.", "ECU Definition"))
    #DTO = property(Int32, 0x6f8)\
    #    .add_attribute(Display("DTO to use", "DTO ID to use for resonses.", "ECU Definition"))
    #BigEndian = property(bool, False)\
    #    .add_attribute(Display("Big Endian", "Use Big Endian byte swapping mode", "ECU Definition"))
    # need to update the below to a list that can be filled by the init function
    CANInterface = property(String, "")\
        .add_attribute(OpenTap.AvailableValues("AvailableCANI"))\
        .add_attribute(Display("Can Interface", "Can interface to use for this ECU.", "CAN Interface", 0.0))
    CANBitRate = property(Int32, 500000)\
        .add_attribute(OpenTap.AvailableValues("BitRatesCANI"))\
        .add_attribute(Display("CAN Bit Rate", "Bit Rate to use for Can interface to this ECU.", "CAN Interface", 0.2))\
        .add_attribute(OpenTap.Unit("bps"))
        
    FDMode = property(bool, False)\
        .add_attribute(Display("FD", "Use CANFD mode", "CAN Interface", 0.3))
    CANFDBitRate = property(Int32, 0)\
        .add_attribute(OpenTap.AvailableValues("BitRatesCANI"))\
        .add_attribute(Display("CANFD Bit Rate", "Bit Rate to use for Can interface to this ECU.", "CAN Interface", 0.4))\
        .add_attribute(OpenTap.Unit("bps"))\
        .add_attribute(OpenTap.EnabledIf("FDMode", True, HideIfDisabled = True))
    BitRateSwitch = property(bool, False)\
        .add_attribute(Display("Bitrate Switch", "CANFD BitRate Switching enable", "CAN Interface", 0.5))\
        .add_attribute(OpenTap.EnabledIf("FDMode", True, HideIfDisabled = True))
    
    Channel = property(String, "0")\
        .add_attribute(OpenTap.SuggestedValues("AvailChannels"))\
        .add_attribute(Display("Channel", "Channel to use for CAN interface.", "CAN Interface", 0.1))
#    @property(Boolean)
#    @attribute(Browsable(False)) # property not visible for the user.
    # This property is based on a C# list of items 'List<int>', List<double>, List<string> can also be used.
    Hide= property(Boolean, True)\
        .add_attribute(OpenTap.Display("Hide CAN Option Stuff", "", "Selectable", 0))
    AvailableCANI = property(List[String], "")\
        .add_attribute(OpenTap.Display("Available Interfaces", "Select which values are available for 'Selectable'.", "Selectable", 2.0))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    BitRatesCANI = property(List[Int32], 0)\
        .add_attribute(OpenTap.Display("Available Bit Rates", "Select which values are available for 'Selectable'.", "Selectable", 2.0))\
        .add_attribute(OpenTap.Unit("bps"))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    AvailChannels = property(List[String], "")\
        .add_attribute(OpenTap.Display("Available Channels", "Select which Channels are available for 'Selectable'.", "Selectable", 2.0))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    #@attribute(Browsable(False)) # property not visible for the user.
   # Measurements = property(List[String], "")
   # Characteristics = property(List[String], "")
    
    bus = None #can.interface.Bus();
    #msgA = can.Message( )
    #msgB = can.Message(  )
    EmptyMessage = can.Message()
            
    PeriodicTask= {0: {'increment': 1, 'offset':  0}}


    NeoviChannels = {
        "HSCAN 1": 1,
        "HSCAN 2": 42,
        "HSCAN 3": 44,
        "HSCAN 4": 61,
        "HSCAN 5": 62,
        "MSCAN 1": 2
    }
    
      



    def __init__(self):

        #self.Measurements = List[String]()
        #self.Characteristics = List[String]()
        super(CANDut, self).__init__() # The base class initializer must be invoked.
        self.Rules.Add(Rule("CANInterface", lambda: self.GetCANInterfaces() != 0, lambda: 'Must Specify a CAN Interface to use'))
        self.Name = "CAN DUT"
#        self.log.Info("creating A2L DB")
#        """ Code to read a2l and fill calibration and measurement lists here"""
        #interfaces = find all interfaces here
#        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
#        self.log.Info("******interfaces found")
        #for ic in interfaceconfigs:
#        self.log.Info("{0} Interfaces returned", len(interfaceconfigs))
        ##########
        #  Need to finish the below to fill out the list of interfaces and channels. 
        #  It probably should check to make sure not adding duplicates too
        self.AvailChannels = List[String]()
        self.AvailableCANI = List[String]()
        self.BitRatesCANI = List[Int32]()
        i = 0
        self.GetCANInterfaces()

        self.Channel = "0"
        self.DTO = 0x6f8
        self.CRO = 0x6f9
        self.FDMode = False
        self.BigEndian = False
        self.BitRatesCANI.Add(5000000)
        self.BitRatesCANI.Add(2000000)
        self.BitRatesCANI.Add(1000000)
        self.BitRatesCANI.Add(500000)
        self.BitRatesCANI.Add(250000)
        self.BitRatesCANI.Add(125000)
        
        #self.AvailChannels.Add(0)
        #self.AvailChannels.Add(1)
        #self.AvailChannels.Add(2)
        #self.AvailChannels.Add(3)
        
        #self.AvailableCANI.Add('kvaser')
        #self.AvailableCANI.Add('neovi')
#        _msgA = can.Message(arbitration_id= 0,  is_extended_id= 0  )
#        _msgB = can.Message(arbitration_id= 0,  is_extended_id= 0  )
       # self.CANBitRate = 500000;
        
######### 
#  Open can and ccp here
#     
#    Interogate python CAN for interfaces and get it ready
#       including listing interfaces in AvailableCANI
#       and listing bitrates in BitRatesCANI
#
# Close the CCP channel here
# any other initialization for pythonccp  

    """ Can Message format"""    
    """         
        __slots__ = (
            "timestamp",
            "arbitration_id",
            "is_extended_id",
            "is_remote_frame",
            "is_error_frame",
            "channel",
            "dlc",
            "data",
            "is_fd",
            "is_rx",
            "bitrate_switch",
            "error_state_indicator",
            "__weakref__",  # support weak references to messages
        )
    """

    def GetCANInterfaces(self):
#        self.log.Info("******interfaces found")
        #for ic in interfaceconfigs:
#        self.log.Info("{0} Interfaces returned", len(interfaceconfigs))
        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
        self.log.Info("******DUT CAN interfaces found")
        self.log.Debug("{0} Interfaces returned", len(interfaceconfigs))
        self.AvailChannels.Clear()
        self.AvailableCANI.Clear()
        for ic in interfaceconfigs:
            self.log.Debug("Interface is :{}".format(ic))
        self.log.Info("{0} Interfaces returned", len(interfaceconfigs))
        ##########
        #  Need to finish the below to fill out the list of interfaces and channels. 
        #  It probably should check to make sure not adding duplicates too
        i = 0
        while i < (len(interfaceconfigs) ):
            inter = interfaceconfigs[i]['interface']
            if (inter == "kvaser"):
                chan = str(interfaceconfigs[i]['channel'])
                #self.log.Debug("Interface {0} Channel {1}", inter, chan)
                if chan not in self.AvailChannels:
                    self.AvailChannels.Add(chan)
            elif (inter != "neovi"):
                chan =  interfaceconfigs[i]['channel']
                if chan not in self.AvailChannels:
                    self.AvailChannels.Add(chan)
            else:
                chan = "1"
                if inter not in self.AvailableCANI:
                    self.AvailChannels.Add("HSCAN 1")
                    self.AvailChannels.Add("HSCAN 2")
                    self.AvailChannels.Add("HSCAN 3")
                    self.AvailChannels.Add("HSCAN 4")
                    self.AvailChannels.Add("HSCAN 5")
                    self.AvailChannels.Add("MSCAN 1")
                    self.log.Info("Interface {0} Channels HSCAN1-5, MSCAN 1", inter)


            if inter not in self.AvailableCANI:
                self.AvailableCANI.Add(inter)
            self.log.Info("Interface {0} Channel {1}", inter, chan)
            #self.log.Debug("{:48} {:12} ", self.AvailableCANI, self.AvailChannels)
            #self.log.Debug("{0}".format(self.AvailableCANI))
            #self.log.Debug("{0}".format( self.AvailChannels))
            i += 1
            



    def Open(self):
        """Called by TAP when the test plan starts.
            add code to open CAN Bus here
        """
        self.EmptyMessage = can.Message(
            timestamp = 0,
            arbitration_id= 0,
            is_extended_id= False,
            is_remote_frame=False,
            is_error_frame= False,
            channel = 0,
            dlc= 0,
            data= [0,0,0,0,0,0,0,0],
            is_fd= False,
            is_rx= True,
            bitrate_switch= False,
            error_state_indicator=True,
        )
        PeriodicTask= {0: {'increment': 1, 'offset':  0}}
        
        self.log.Info(self.Name + " Opening")
        #can_filters = [{"can_id": 0x6f8, "can_mask": 0x7ff, "extended": True}]

        if (self.CANInterface == "neovi"):
            _channel = self.NeoviChannels[self.Channel]
        else:
            _channel = self.Channel
        self.log.Debug("Opening CAN Interface {0}, Channel {1}, bitrate {2}".format(self.CANInterface, self.Channel, self.CANBitRate))
        #self.transport = ccp.CANTransport(self.CANInterface, _channel, self.CANBitRate)

        self.bus = can.interface.Bus(interface=self.CANInterface, app_name= None, channel=_channel, bitrate=self.CANBitRate)
        #self.bus.set_filters(can_filters)
        ######### 
        #  Open ccp here
        #   Connect to CCP ECU
        # any other initialization for pythonccp  after connect

        self.log.Info(self.Name + " Opened")

    def Close(self):
        """Called by TAP when the test plan ends.
            Add code to close CAN bus here
        """
        ######
        # Close the CCP channel here
        ##
        self.bus.shutdown()
        self.log.Info(self.Name + " Closed")
     
# works as test    def SendCAN(self, arbitration_id=0xC0FFEE, data=44444, is_extended_id=True):
    def SendCAN(self, arbitration_id=0xC0FFEE, dataout=[1,2,3,4,5,6,7,8], is_extended_id=True, is_fd=False):
        """enter function to send here"""
        #convert physical to data first
        # Download data now
        #ccp_ecu.dnload(self.CRO, size, data)
        """ Can Message format"""    
        """         
            __slots__ = (
                "timestamp",
                "arbitration_id",
                "is_extended_id",
                "is_remote_frame",
                "is_error_frame",
                "channel",
                "dlc",
                "data",
                "is_fd",
                "is_rx",
                "bitrate_switch",
                "error_state_indicator",
                "__weakref__",  # support weak references to messages
            )
        """
        self.log.Debug("package Message for interface {0}, to CANID  {1} with data {2}", self.bus.channel_info, arbitration_id, dataout)
        #_msgSend = can.Message( arbitration_id=arbitration_id, data=[1,2,3,4,5,6,7,8], is_extended_id=False)
        _msgSend = can.Message( 
            arbitration_id=arbitration_id, 
            is_extended_id= is_extended_id,
            is_remote_frame=False,
            is_error_frame= False,
            channel = None,
            dlc= len(dataout),
            data= dataout,
            is_fd= is_fd,
            is_rx= False,
            #bitrate_switch= False,
            error_state_indicator=False
        )

        #_msgSend = can.Message( arbitration_id=arbitration_id, data=[data[0], data[1],data[2],data[3],data[4],data[5]], is_extended_id=is_extended_id)
        self.log.Debug("Lets sendCAN Message sent to bus {0} for CANID  {1} of length {2} with data {3}. Errorcode {4}", self.bus.channel_info, _msgSend.arbitration_id, _msgSend.dlc, _msgSend, can.CanError)
        try:
            self.log.Debug("GO try")
            self.bus.send(_msgSend)
            self.log.Info("CAN Message sent on  {0} to CANID  {1}", self.bus.channel_info, _msgSend.dlc)
            
        except can.CanError:
            self.log.Info("Message not sent error code {0}", can.CanError)

# Send periodic CAN messages with possibility to increment a byte every message
# need to find a way to have every call use different increment settings
    def SendPeriodicCAN(self, arbitration_id=0xC0FFEE, dataout=[1,2,3,4,5,6,7,8], is_extended_id=True, SendPeriod=1.0, SendDuration=10, IncrementByte=False, Increment= 1, ByteLocation=1, is_fd=False):
        """enter function to send here"""
        
        """ Can Message format"""    
        """         
            __slots__ = (
                "timestamp",
                "arbitration_id",
                "is_extended_id",
                "is_remote_frame",
                "is_error_frame",
                "channel",
                "dlc",
                "data",
                "is_fd",
                "is_rx",
                "bitrate_switch",
                "error_state_indicator",
                "__weakref__",  # support weak references to messages
            )
        """
        self.log.Debug("package periodic Message for bus {0} to CANID  {1} every {4} seconds of length {2} with data {3}", self.bus.channel_info, arbitration_id, 4, dataout, SendPeriod)
        
        _msgSend = can.Message( arbitration_id=arbitration_id, data=dataout, channel=None, is_extended_id=is_extended_id, is_fd=is_fd)
        
        self.log.Debug("Lets sendCAN Message sent to bus {0} for CANID  {1}  every {4} seconds of length {2} with data {3}", self.bus.channel_info, _msgSend.arbitration_id, _msgSend.dlc, _msgSend, SendPeriod)
        try:
            self.log.Debug("GO try")
            # should add callback support at some point
            if (IncrementByte):
                self.PeriodicTask.update({arbitration_id:{'increment': Increment, 'offset': ByteLocation}});
                self.bus.send_periodic(_msgSend, SendPeriod, SendDuration, modifier_callback=self.update_message)
                self.log.Info("CAN Message sent on  {0} to CANID  {1}", self.bus.channel_info, _msgSend.dlc)

            else:
                self.bus.send_periodic(_msgSend, SendPeriod, SendDuration)
                self.log.Info("CAN Message sent on  {0} to CANID  {1}", self.bus.channel_info, _msgSend.dlc)
            
        except can.CanError:
            self.log.Info("Message not sent error code {0}", can.CanError)

    def update_message(self, message: can.Message) -> None:
        #need a way to have multiple incrment instances
        _offset = self.PeriodicTask[message.arbitration_id]['offset']
        _increment = self.PeriodicTask[message.arbitration_id]['increment']
        message.data[_offset] = (message.data[_offset] + _increment) % 0x100;
    
    def StopPeriodicCAN(self):
        self.bus.stop_all_periodic_tasks()

    def ReadAnyCAN(self, timeout = 1.0):
        """ enter function here """
        self.log.Debug("Read Any CAN Message start")
        self.log.Debug("timeout= {0}", timeout)
        self.bus.set_filters()
        #msg = Message()
        ##### Add code to get value from CCCP here
        _msgA = self.bus.recv(timeout)
        time.sleep(0.1)
        
        self.log.Debug("Message Read function done")
        if _msgA is not None:
            self.log.Debug("Message read {0}", _msgA.arbitration_id)
            valueout = _msgA.arbitration_id
            self.log.Info("Read CAN Message {0} {1} {2} {3}", _msgA.arbitration_id, _msgA.channel, _msgA.dlc, _msgA.data[0])
#        
        return _msgA


    def ReadFilteredCAN(self, CANid = 0x6f8, CANMask = 0x7FF, CANExtended = False, timeout = 1.0):
        """ enter function here """
        self.log.Debug("Read Filter is  CAN ID: {0}, Timeout: {1} Mask: {2:8x} Extended : {3}", CANid, timeout, CANMask, CANExtended)
        ##### Add code to get value from CCCP here
        can_filters = [{"can_id": CANid, "can_mask": CANMask, "extended": CANExtended}]
        self.bus.set_filters(can_filters)
        #_msgB = can.Message(  )
        # print all incoming messages, which includes the ones sent,
        # since we set receive_own_messages to True
        # assign to some variable so it does not garbage collected
        #notifier = can.Notifier(bus, [can.Printer()])  # pylint: disable=unused-variable
        time.sleep(0.1)
        dummymsg = self.bus.recv(timeout)
        _msgB = dummymsg # = self.bus.recv(timeout)
        self.log.Debug("Message Dummy read {0}", dummymsg)
            
        
        self.log.Debug("Message Read filtered function done")
        if _msgB is not None:
            self.log.Debug("Message filt read {0}", _msgB)
            self.log.Info("Read filtered CAN Message {0} {1} {2} {3} {4}", CANid, _msgB.arbitration_id, _msgB.channel, _msgB.dlc, _msgB.data[0])
            return dummymsg
        else:
            self.log.Debug("No Message read {0}", _msgB)
            #self.log.Info("Read filtered CAN Message {0} {1} {2} {3} {4}", CANid, _msgB.arbitration_id, _msgB.channel, _msgB.dlc, _msgB.data[0])
            return self.EmptyMessage
 
       #dummymsg = _msgB # Message(arbitration_id=0x6f4, is_extended_id=False, is_error_frame=False, channel=0, data = None)
        return dummymsg
#        #return _msgB