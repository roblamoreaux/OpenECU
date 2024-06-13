﻿"""
 A ECU example of how to define a DUT driver.
"""
from opentap import *
import System
from System import String
from System.Collections.Generic import List
from OpenTap import Log, DisplayAttribute, Display, FilePathAttribute, FilePath
from System import Array, Double, Byte, Int32, String, Boolean # Import types to reference for generic methods
import os

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
from pprint import pprint
import struct

from pythonccp import ccp
from pythonccp.logger import Logger
from pythonccp.master import Master

import can
from can.bus import BusState
from can import *

MTA0 = 0
MTA1 = 1

#db = DB()

@attribute(OpenTap.Display("OpenECU DUT", "An OpenECU DUT driver.", "OpenECU DUTs"))
class ECUDut(Dut):
    # Add a Firmware version setting which can be configured by the user.
    Firmware = property(String, "1.0.2")\
        .add_attribute(OpenTap.Display( "Firmware Version", "The firmware version of the DUT.", "Common"))
    """
    create fields for 
        selecting A2L file
        selecting CAN interface and parameters (use list)
        Selecing DTO
        Selecting CRO
        other stuff

        Add code to check A2L file is still current so it can be updated if not instead of loading every Open

        c:\\OpenTAP\\ASAP2_Demo_V161
        c:\\OpenTAP\\LaforgeTestApp_CCU_tool_generic
    """
    A2LFilePath = property(String, None)\
        .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Open, ".a2l"))\
        .add_attribute(Display("A2L File Path", "File path for ECU Definition.", "ECU Definition",0.1))
    CRO = property(Int32, 0x6f9)\
        .add_attribute(Display("CRO to use", "CRO ID to use for commands.", "ECU Definition",0.2))
    DTO = property(Int32, 0x6f8)\
        .add_attribute(Display("DTO to use", "DTO ID to use for resonses.", "ECU Definition",0.3))
    Station = property(Byte, 0)\
        .add_attribute(Display("Station ID to use", "Station ID to use for resonses.", "ECU Definition",0.35))
    BigEndian = property(bool, False)\
        .add_attribute(Display("Big Endian", "Use Big Endian byte swapping mode", "ECU Definition",0.4))
    # need to update the below to a list that can be filled by the init function
    CANInterface = property(String, "kvaser")\
        .add_attribute(OpenTap.AvailableValues("AvailableCANI"))\
        .add_attribute(Display("Can Interface", "Can interface to use for this ECU.", "CAN Interface",1.0))

    Channel = property(String, "")\
        .add_attribute(OpenTap.SuggestedValues("AvailChannels"))\
        .add_attribute(Display("Channel", "Channel to use for CAN interface.", "CAN Interface", 1.05))

#    CANBitRate = property(Int32, 500000)\
#        .add_attribute(OpenTap.AvailableValues("BitRatesCANI"))\
#        .add_attribute(Display("Can Bit Rate", "Bit Rate to use for Can interface to this ECU.", "CAN Interface",1.1))
    CANBitRate = property(Int32, 500000)\
        .add_attribute(OpenTap.AvailableValues("BitRatesCANI"))\
        .add_attribute(Display("Can Bit Rate", "Bit Rate to use for Can interface to this ECU.", "CAN Interface", 1.1))\
        .add_attribute(OpenTap.Unit("bps"))

    FDMode = property(bool, False)\
        .add_attribute(Display("FD", "Use CANFD mode", "CAN Interface",1.1))
    CANFDBitRate = property(Int32, 2000000)\
        .add_attribute(OpenTap.AvailableValues("BitRatesCANI"))\
        .add_attribute(Display("CAN FD Bit Rate", "Bit Rate to use for Can interface to this ECU.", "CAN Interface", 1.3))\
        .add_attribute(OpenTap.Unit("bps"))\
        .add_attribute(OpenTap.EnabledIf("FDMode", True, HideIfDisabled = True))
    BitRateSwitch = property(bool, False)\
        .add_attribute(Display("Bitrate Switch", "CANFD BitRate Switching enable", "CAN Interface", 1.4))\
        .add_attribute(OpenTap.EnabledIf("FDMode", True, HideIfDisabled = True))


#    @property(Boolean)
#    @attribute(Browsable(False)) # property not visible for the user.
    # This property is based on a C# list of items 'List<int>', List<double>, List<string> can also be used.
    AvailableCANI = property(List[String], "")\
        .add_attribute(OpenTap.Display("Available Interfaces", "Select which values are available for 'Selectable'.", "Selectable", 9.0))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    #BitRatesCANI = property(List[Int32], 0)\
    #    .add_attribute(OpenTap.Display("Available Bit Rates", "Select which values are available for 'Selectable'.", "Selectable"))
    BitRatesCANI = property(List[Int32], None)\
        .add_attribute(OpenTap.Display("Available Bit Rates", "Select which values are available for 'Selectable'.", "Selectable", 9.1))\
        .add_attribute(OpenTap.Unit("bps"))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    
    #@attribute(Browsable(False)) # property not visible for the user.
    Hide= property(Boolean, True)\
        .add_attribute(OpenTap.Display("Hide Optional Stuff", "", "Selectable", 0))
    AvailChannels = property(List[String], 0)\
        .add_attribute(OpenTap.Display("Available Channels", "Select which Channels are available for 'Selectable'.", "Selectable", 9.2))\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    Measurements = property(List[String], "")\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    Characteristics = property(List[String], "")\
        .add_attribute(OpenTap.EnabledIf("Hide", False, HideIfDisabled = True))
    
    master = None
    #db = DB()
    datatypesize = {
        "UBYTE": 1,
        "SBYTE": 1,
        "UWORD": 2,
        "SWORD": 2,
        "ULONG": 4,
        "SLONG": 4,
        "A_UINT64": 8,
        "A_INT64": 8,
        "FLOAT16_IEEE": 2,
        "FLOAT32_IEEE": 4,
        "FLOAT64_IEEE": 8,}

    NeoviChannels = {
        "HSCAN 1": 1,
        "HSCAN 2": 42,
        "HSCAN 3": 44,
        "HSCAN 4": 61,
        "HSCAN 5": 62,
        "MSCAN 1": 2
    }
    
    def __init__(self):

        self.Measurements = List[String]()
        self.Characteristics = List[String]()
        self.Rules.Add(Rule("A2LFilePath", lambda: self.Checkfilename() != 0, lambda: 'Must Specify a file name for the A2LFile'))
        self.db = DB()
#        self.Measurements.Clear()
#        self.Characteristics.Clear()
        super(ECUDut, self).__init__() # The base class initializer must be invoked.
        self.HighPowerOn = False
        self.Name = "OpenECU DUT"
        

        #self.LoadA2L(self.A2LFilePath, initdb)
        #self.CloseA2LECU()
        #initdb.close()
        #self.log.Info(self.Name + " Closed")


        self.DTO = 0x6f8;
        self.CRO = 0x6f9;
        self.FDMode = False;
        self.BigEndian = False;
        
        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
        self.log.Info("******interfaces found")
        for ic in interfaceconfigs:
            self.log.Debug("Interface is :{}".format(ic))
        self.log.Info("{0} Interfaces returned", len(interfaceconfigs))
        ##########
        #  Need to finish the below to fill out the list of interfaces and channels. 
        #  It probably should check to make sure not adding duplicates too
        self.AvailChannels = List[String]()
        self.AvailableCANI = List[String]()
        self.BitRatesCANI = List[Int32]()
        i = 0
        self.GetCANInterfaces()
        
        self.Channel = "0";
        self.BitRatesCANI.Add(5000000)
        self.BitRatesCANI.Add(2000000)
        self.BitRatesCANI.Add(1000000)
        self.BitRatesCANI.Add(500000)
        self.BitRatesCANI.Add(250000)
        self.BitRatesCANI.Add(125000)
        
        self.oldA2LFile = self.A2LFilePath
#        self.AvailChannels.Add(0)
#        self.AvailChannels.Add(1)
#        self.AvailChannels.Add(2)
#        self.AvailChannels.Add(3)
        
        #self.AvailableCANI.Add('kvaser')
        #self.AvailableCANI.Add('neovi')

######### 
#  Open can and ccp here
#     
#    Interogate python CAN for interfaces and get it ready
#       including listing interfaces in AvailableCANI
#       and listing bitrates in BitRatesCANI
#
# Close the CCP channel here
# any other initialization for pythonccp  

    def GetCANInterfaces(self):
        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
        self.log.Info("******interfaces found")
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
            

    
        
    def Checkfilename(self):
        initdb = DB()
        A2LFile, _ext = os.path.splitext(self.A2LFilePath)
        self.GetCANInterfaces()
        _curdir = os.getcwd()
        _directory = os.path.dirname(self.A2LFilePath)
        self.log.Info("Filename is " + os.path.abspath(A2LFile))
         
        self.log.Debug('directory = {0} Filename = {1}'.format(_directory, A2LFile))
        if ((os.path.isfile(A2LFile + ".a2l") )):
            self.log.Info("A2L does exist")
            _a2ldbExists = False
            _a2lExists = True
            self.A2LFilePath = os.path.abspath(A2LFile)
        if ((os.path.isfile(A2LFile + ".a2ldb"))):
            self.log.Info("A2LDB does exist")
            _a2ldbExists = True
            self.A2LFilePath = os.path.abspath(A2LFile)
        if ((os.path.isfile(A2LFile + ".a2ldb-journal"))):
            self.log.Error("A2LDB-journal does exist")
            _a2ldbExists = True
#            self.CloseA2LECU( initdb)
#            self.db.close()
            #os.remove(A2LFile + ".a2ldb-journal")
            return -9
        self.log.Info("{0} {1}: LM={2}, LC={3}".format(_a2lExists, _a2ldbExists,self.Measurements.Count,self.Characteristics.Count))
        #if ((_a2lExists) and (not _a2ldbExists ) and ((len(self.Measurements) == 0) or (len(self.Characteristics) == 0))):
        if ((self.A2LFilePath != self.oldA2LFile) and (_a2lExists) or ((self.Measurements.Count <= 1) or (self.Characteristics.Count <= 1))):
            self.LoadA2L(self.A2LFilePath, initdb)
            self.CloseA2LECU( initdb)
        return 1


    def Open(self):
        """Called by TAP when the test plan starts.
            add code to open CAN Bus here
        """
        #rundb = DB()
        self.log.Info(" {0} Opening {1} channel {2} bitrate {3}", self.Name , self.CANInterface, self.Channel, self.CANBitRate)
        ######### 
        #  Open ccp here
        #   Connect to CCP ECU
        # any other initialization for pythonccp  after connect
        if ((os.path.isfile(self.A2LFilePath + ".a2ldb-journal"))):
            self.log.Error("A2LDB-journal does exist")
            os.remove(self.A2LFilePath + ".a2ldb-journal")
        self.log.Debug("Opening file {0} and db= xxxx".format(self.A2LFilePath))
        self.LoadA2L(self.A2LFilePath, self.db)
        if (self.CANInterface == "neovi"):
            _channel = self.NeoviChannels[self.Channel]
        else:
            _channel = self.Channel
        self.log.Debug("Opening CAN Interface {0}, Channel {1}, bitrate {2}".format(self.CANInterface, _channel, self.CANBitRate))
        self.transport = ccp.CANTransport(self.CANInterface, _channel, self.CANBitRate)
        #transport = ccp.CANTransport()
        #transport = ccp.CANTransport("neovi", 0, 500000)
        self.master = Master(self.transport)

        self.log.Info(self.Name + " Opened")

    def Close(self):
        """Called by TAP when the test plan ends.
            Add code to close CAN bus here
        """
        self.log.Info(self.Name + " Closing")
        self.CloseA2LECU(self.db)
        self.db.close()
        self.master.close()
        self.transport.close()
        self.log.Info(self.Name + " Closed")
        
        ######
        # Close the CCP channel here
        ##
        #self.master.disconnect(self.CRO, 1, self.Station)
        #self.CloseA2LECU()
        
        self.log.Info(self.Name + " Closed")





    def LoadA2L(self, A2LFile = "", dbo = None):
        # this code expands the macros used by FilePath.
        #fileName = self.A2LFilePath.Expand(A2LFile)
        
        # Create directory if not exists
        directory = os.path.dirname(A2LFile)
#        if not os.path.exists(directory):
#            os.makedirs(directory)

        self.log.Info("creating A2L DB")
        """ Code to read a2l and fill calibration and measurement lists here"""
#        self.db = DB()
        #self.log.Info("Opening A2L filename" + fileName)
        self.log.Info("Opening A2L directory" + directory)
        
        self.log.Info("Opening A2L" + A2LFile)
        self.log.Info(A2LFile + " Opening")
#### Needs error checking added including try  and catch since it is not graceful if the file is bad
        _a2ldbExists = False
        try:
            if ((os.path.isfile(A2LFile + ".a2l") )):
                self.log.Info("A2L does exist")
            if ((os.path.isfile(A2LFile + ".a2ldb"))):
                self.log.Info("A2LDB does exist")
                _a2ldbExists = True
            if ((os.path.isfile(A2LFile + ".a2ldb-journal"))):
                self.log.Error("A2LDB-journal does exist")
                _a2ldbExists = True
                os.remove(A2LFile + ".a2ldb-journal")
                return -9
            if (_a2ldbExists ):
                self.log.Info("A2LDB Opening existing  {0}", A2LFile)
                self.session = dbo.open_existing(A2LFile)
                #session = dbo.open_existing(fileName)
                
            else:
                self.log.Info("A2LDB Creating {0}", A2LFile)
                self.session = dbo.open_create(A2LFile, encoding="ansi")
#            session = db.import_a2l(self.A2LFilePath, encoding="ansi", local = True, remove_existing=True)
        except Exception as e:
            self.log.Error(A2LFile + " Failed to Open")
            self.log.Debug(e)
        
        self.log.Info("A2L opened")
        
        try:
            #session = db.open_create("C:\\OpenTAP\\LaforgeTestApp_CCU_tool_generic")
            #self.log.Info("Measurements found")
            self.Measurements.Clear()
            _measurements = self.session.query(model.Measurement).order_by(model.Measurement.name).all()
            self.log.Info("****** {0} Measurements found.", len(_measurements))
            for m in _measurements:
                self.Measurements.Add(m.name)
                #self.log.Debug("{:48} {:12} 0x{:08x}".format(m.name, m.datatype, m.ecu_address.address))
        except Exception as e:
            self.log.Error("Measurements not read")
            self.log.Debug(e)
        self.Measurements.Sort
        try:
            self.Characteristics.Clear()
            _characteristics = self.session.query(model.Characteristic).order_by(model.Characteristic.name).all()
            self.log.Info("****** {0} Characteristics found", len(_characteristics))
            for m in _characteristics:
                self.Characteristics.Add(m.name)
                #self.log.Debug("{:48} {:12} 0x{:08x}".format(m.name, m.type, m.address))
        except Exception as e:
            self.log.Error("Characteristics not read")
            self.log.Debug(e)
        self.Characteristics.Sort

    def CloseA2LECU(self, dbo):
        dbo.close()

    def WriteCalibration(self, cal = "", value = 0):
        """enter function to send here"""
        #convert physical to data first
        # Download data now
        #ccp_ecu.dnload(self.CRO, size, data)
        self.log.Debug("Write Calibration Measurement  {0}  {1}", cal, value)
        #self.log.Debug("write Calibration  " + cal)
        ##### Add code to get value from CCCP here
        #get data size first
        # Upload data now
        #value = ccp_ecu.upload(self.CRO, size)
        self.master.connect(self.CRO, 0, self.DTO)
        #value = 1075142656
        _mstring = cal
        meas = Characteristic(self.db.session, _mstring)
#        self.log.Debug("Write Calibration datatype {0} ", meas.type)
#        self.log.Debug("Write Calibration compuMethod {0} ", meas.compuMethod.name)
#        self.log.Debug("Write Calibration address {0} ", meas.address)
#        self.log.Debug("Write Calibration byteorder {0} ", meas.byteOrder)
#        self.log.Debug("Write Cal datatype = {0}", meas.record_layout_components[0][1]['datatype'])
        #self.log.Debug("Read Measurement {0} ", meas)
        compu = CompuMethod(self.db.session, meas.compuMethod.name)
        dtype = meas.deposit.fncValues['datatype']
        size = self.datatypesize[dtype]
#        self.log.Debug("Write Calibration convtype {0} {1}, {2}",  compu.conversionType, dtype, size)
#        self.log.Debug("Write Calibration compumethod data physical value {0} ", value)
        intvalue = compu.physical_to_int(value) 
#        self.log.Debug("Write Calibration compumethod data word {0} ", intvalue)
#       
        self.master.setMta(self.CRO,meas.address, meas.ecuAddressExtension)

        retvalue = self.master.dnload(canID=self.CRO, size=size, value=intvalue, datatype=dtype, byteorder=meas.byteOrder)
        self.master.disconnect(self.CRO, 0, self.Station)
        return retvalue


    def WriteMeasurement(self, cal = "", value = 0):
        """ enter function here"""
        #convert physical to data first
        # Download data now
        """ enter function here """
        self.log.Debug("Write  Measurement  {0}  {1}", cal, value)
        ##### Add code to get value from CCCP here
        #get data size first
        # Upload data now
        self.master.connect(self.CRO, 0, self.DTO)
        #value = 1075142656
        _mstring = cal;
        meas = Measurement(self.db.session, _mstring)
#        self.log.Debug("Write Measurement datatype {0} ", meas.datatype)
#        self.log.Debug("Write Measurement compuMethod {0} ", meas.compuMethod.name)
#        self.log.Debug("Write Measurement address {0} ", meas.ecuAddress)
#        self.log.Debug("Write Measurement size {0} ", meas.datatype)
#        self.log.Debug("Write Measurement byteorder {0} ", meas.byteOrder)
        compu = CompuMethod(self.db.session, meas.compuMethod.name)
#        self.log.Debug("Write Measurement convtype {0} ",  compu.conversionType)
#        self.log.Debug("Write Measurement compumethod data physical value {0} ", value)
        intvalue = compu.physical_to_int(value) 
#        self.log.Debug("Write Measurement compumethod data word {0} ", intvalue)
        #phyvalue = meas.compuMethod.int_to_physical(value)# compu.physical_to_int("Sinus") == 3
        # compu.int_to_physical(10) is None
        #self.log.Info("Read Measurement {0}", phyvalue)
#       
        self.master.setMta(self.CRO,meas.ecuAddress, meas.ecuAddressExtension)

        retvalue = self.master.dnload6(canID=self.CRO, value=intvalue, datatype=meas.datatype, byteorder=meas.byteOrder)

        self.master.disconnect(self.CRO, 0, self.Station)
        return retvalue

    def ReadMeasurement(self, cal = ""):
        """ enter function here """
#        self.log.Debug("Read Measurement  " + cal)
        ##### Add code to get value from CCCP here
        #get data size first
        # Upload data now
        self.log.Debug("dto={0}, CRO={1}".format(self.DTO, self.CRO))
        self.master.connect(self.CRO, 0, self.DTO)
        _mstring = cal;
        meas = Measurement(self.db.session, _mstring)
#        self.log.Debug("Read Measurement datatype {0} ", meas.datatype)
#        self.log.Debug("Read Measurement compuMethod {0} ", meas.compuMethod.name)
        size = self.datatypesize[meas.datatype]

#        self.log.Debug("Read Measurement size {0} ", )
#        self.log.Debug("Read Measurement byteorder {0} ", meas.byteOrder)
        value = self.master.shortUp(self.CRO, self.DTO, size, meas.ecuAddress, meas.ecuAddressExtension, meas.datatype, meas.byteOrder)
#        self.log.Debug("read returned {0}xxx", value)
        
        compu = CompuMethod(self.db.session, meas.compuMethod.name)
#        self.log.Debug("Read Measurement convtype {0} ",  compu.conversionType)
        phyvalue = compu.int_to_physical(value) 
#        self.log.Debug("Read Measurement compumethod {0} ", value)
        phyvalue = meas.compuMethod.int_to_physical(value)# compu.physical_to_int("Sinus") == 3
        # compu.int_to_physical(10) is None
        self.log.Debug("Read Measurement {0} {1}", cal, phyvalue)
#        self.master.disconnect(self.CRO, 0, self.Station)
        return phyvalue

    #@method(Double)
    def ReadCalibration(self, cal = ""):
        """ enter function here """
#        self.log.Info("Read Calibration  " + cal)
        #get data size first
        # Upload data now
        self.master.connect(self.CRO, 0, self.DTO)
        meas = Characteristic(self.db.session, cal)
#        self.log.Debug("Read Measurement Address {0} ", meas.address)
#        self.log.Debug("Read Measurement Type {0} ", meas.type)
#        self.log.Debug("Read cal size {0} ", meas.type)
#        self.log.Debug("Read cal byteorder {0} ", meas.byteOrder)

        dtype = meas.deposit.fncValues['datatype']
        size = self.datatypesize[dtype]

#        self.log.Debug("Read Calibration compuMethod {0} ", meas.compuMethod.name)
        value = self.master.shortUp(self.CRO, self.DTO, size, meas.address, meas.ecuAddressExtension, dtype, meas.byteOrder)
#        self.log.Debug("read returned {0}", value)
        
        ############# Probably should add code to properly convert the format here

        compu = CompuMethod(self.db.session, meas.compuMethod.name)
#        self.log.Debug("Read Calibration convtype {0} ",  compu.conversionType)
        phyvalue = compu.int_to_physical(value) 
#        self.log.Debug("Read Calibration compumethod {0} {1} ", value, phyvalue)
        phyvalue = meas.compuMethod.int_to_physical(value)
        # compu.int_to_physical(10) is None
        self.log.Debug("Read Calibration meas: {0} {1} ", cal, phyvalue)
        return phyvalue
        value = 999.0
#        self.log.Debug("Read Calibration {0} ", value)
        return value
