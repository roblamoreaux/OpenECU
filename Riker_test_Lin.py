""" Example of how a python class can be written. """
import sys
import time
import opentap
import clr
clr.AddReference("System.Collections")
from System.Collections.Generic import List
from opentap import *
from canlib import Frame, linlib
import ldfparser
import os

import OpenTap 
import math
from OpenTap import Log, AvailableValues, EnabledIfAttribute

## Import necessary .net APIs
# These represents themselves as regular Python modules but they actually reflect
# .NET libraries.
import System
from System import Array, Double, Byte, Int32, String, Boolean # Import types to reference for generic methods
from System.ComponentModel import Browsable # BrowsableAttribute can be used to hide things from the user.
#import System.Xml
#from System.Xml.Serialization import XmlIgnore

from .ECUDut import ECUDut
from .ECUSettings import ECUSettings
from .ReadMeasurement import ReadMeasurement

import System
from System import Array, Double, Byte, Int32, String, Boolean # Import types to reference for generic methods
from System.ComponentModel import Browsable # BrowsableAttribute can be used to hide things from the user.

@attribute(OpenTap.Display("Lin Receiver", "Reads LIN Frame.", "Riker DV Tests"))
@attribute(OpenTap.AllowAnyChild())
class RunTests(TestStep):
    Dut = property(ECUDut, None).add_attribute(OpenTap.Display( "DUT", "The DUT to use in the step.", "Resources"))
    
    LDFFrame = property(String, "")\
        .add_attribute(OpenTap.AvailableValues("LDFFrameList"))\
        .add_attribute(OpenTap.Display("Frame", "Provide an existing frame from Riker Application", "Frame and Signals",0))
    
    LDFFrameList = property(List[String], "")\
        .add_attribute(OpenTap.Display("Available Frames", "Select which values are available for 'Selectable'.", "Selectable", 0))\
        
    Signal = property(String, "")\
        .add_attribute(OpenTap.AvailableValues("Signals_List"))\
        .add_attribute(OpenTap.Display("Signals", "Provide an existing signal from frame", "Frame and Signals",0))
    
    Signals_List = property(List[String], "")\
        .add_attribute(OpenTap.Display("Available Signals", "Select which values are available for 'Selectable'.", "Selectable", 0))\
        
    LINBitRate = property(Int32, 19200)\
        .add_attribute(OpenTap.Display("Lin Bit Rate", "Bit Rate to use for Lin interface to this ECU.", "Lin Interface", 0))\
        .add_attribute(OpenTap.Unit("bps"))
    
    Signal_only = property(bool, False)\
        .add_attribute(OpenTap.Display("Signal Only", "Check box to only display the signal selected in frame", "Frame and Signals",0))
    
    Master_Kvaser_Channel = property(Int32, 1)\
    .add_attribute(OpenTap.Display("Master_Kvaser_Channel", "Select Lin Channel for Master", "Channels",0))

    Slave_Kvaser_Channel = property(Int32, 1)\
    .add_attribute(OpenTap.Display("Slave_Kvaser_Channel", "Select Lin Channel for Slave", "Channels",0))
    
    
    def __init__(self):
        super().__init__() # The base class initializer must be invoked.
        self.log.Info("Init ReadMeasurement message")
        self.Logging = OpenTap.Enabled[String]()
        self.LDFFrameList = List[String]() # Initalize a list to store all LDF Frames
        self.Signals_List = List[String]() # Initalize a list to store all Signals of an Frame
        self.LDFFrameList = self.Dut.log_ldf_file_path() # Store all Frames in this list.
        

        self.Rules.Add(Rule("LDFFrame", lambda: self.signal_list_creator() , lambda: 'Frame not specified'))
        
        self.Rules.Add(Rule("Signals", lambda: self.signal_selector() , lambda: 'Signal not specified'))

        self.Rules.Add(Rule("Master_selector", lambda: self.master_selector() , lambda: 'Master not specified'))

        self.Rules.Add(Rule("Slave_selector", lambda: self.slave_selector() , lambda: 'Slave not specified'))

        # self.master, self.slave = self.init_lin_bus(self.Master_Kvaser_Channel,self.Slave_Kvaser_Channel,self.LINBitRate)

    def signal_list_creator(self):
        ldf = ldfparser.parse_ldf_to_dict(os.path.abspath(self.Dut.LDFFilePath))
        temp_list = []
        self.Signals_List.Clear()
        for frame in range(len(ldf['frames'])):
            if ldf['frames'][frame]['name'] == self.LDFFrame:
                for signals in ldf['frames'][frame]['signals']:
                    temp_list.append(signals)
        for signals in temp_list:
            self.Signals_List.Add(signals['signal'])
        
        return True, self.Signals_List
    
    def signal_selector(self):
        if self.Signal in self.Signals_List:
            self.log.Info("Signal selected")
            return True, self.Signal
        
    def master_selector(self):
        if self.Master_Kvaser_Channel in [0,1]:
            self.log.Info(f"Master channel {self.Master_Kvaser_Channel}")
            return True, self.Master_Kvaser_Channel
        
    def slave_selector(self):
        if self.Slave_Kvaser_Channel in [0,1]:
            self.log.Info(f"Slave channel {self.Slave_Kvaser_Channel}")
            return True, self.Slave_Kvaser_Channel
            
    def PrePlanRun(self):
        super().PrePlanRun()
        self.master, self.slave = self.init_lin_bus(self.Master_Kvaser_Channel,self.Slave_Kvaser_Channel,self.LINBitRate)


    def Run(self):
         super().Run()
         self.log.Info("Logging LDFFrame: {}".format(self.LDFFrame))
         self.LIN_receiver(self.slave, self.master, self.LDFFrame, self.Dut.LDFFilePath, self.Signal, self.Signal_only)
         


    def init_lin_bus(self, master_channel_number=int, slave_channel_number=int, bit_rate=int):

        print (f"master={master_channel_number}, slave={slave_channel_number}")
        # open the first channel as Master, using helper function
        master = linlib.openMaster(master_channel_number, bps=bit_rate)

        # open the next channel as a Slave, using helper function
        slave = linlib.openSlave(slave_channel_number)

        master.busOn()
        slave.busOn()

        # configure channels to use LIN 2.0
        slave.setupLIN(flags=linlib.Setup.ENHANCED_CHECKSUM | linlib.Setup.VARIABLE_DLC)
        master.setupLIN(flags=linlib.Setup.ENHANCED_CHECKSUM | linlib.Setup.VARIABLE_DLC)

        return master, slave

    # function to request the message and print it
    def LIN_receiver(self, slave, master, frame_name=str, ldf_file_path=str, signal=str, signals_only=bool):
        ldf = ldfparser.parse_ldf(path=ldf_file_path)
        while True:
            slave.writeWakeup()
            ldf_frame = ldf.get_unconditional_frame(frame_name)
            master.requestMessage(ldf_frame.frame_id)
            frame = master.read(timeout=100)
            if bytearray(frame.data) != b'' and len(bytearray(frame.data))>2 and frame.id==ldf_frame.frame_id:
                print(frame)
                data = ldf_frame.decode(frame.data)
                if signals_only == False:
                    for keys, values in data.items():
                        self.log.Info(f'Signal: {keys} Value: {values}')
                if signals_only == True:
                    for keys, values in data.items():
                        if keys == signal:
                            self.log.Info(f'Signal: {keys} Value: {values}')
                
                self.UpgradeVerdict(OpenTap.Verdict.Pass)
                break
            else:
                print('waiting')