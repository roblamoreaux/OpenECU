""" Example of how a python class can be written. """
import sys
import opentap
import clr
clr.AddReference("System.Collections")
from System.Collections.Generic import List
from opentap import *
import time
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
import can
from can.bus import BusState
from can import *

from .CANDut import CANDut
import struct
#from .CANSettings import CANSettings


# Here is how a test step plugin is defined: 

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("ReadFilterCAN", "Read Filtered CAN message from CAN DUT.", "CAN Steps"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class ReadAnyCAN(TestStep): # Inheriting from opentap.TestStep causes it to be a test step plugin.
    # Add properties (name, value, C# type)
    
    Dut = property(CANDut, None).add_attribute(OpenTap.Display( "DUT", "The DUT to use in the step.", "Resources"))
    

    #CANID = property(Int32, None)\
    #    .add_attribute(OpenTap.Display("CAN ID", "Calibration to read.", "Signal to Read"))
    # This property is based on a C# list of items 'List<int>', List<double>, List<string> can also be used.
    #Available = Dut.Characteristic
    #Available = List[String]()
    
    #Available = property(List[String], "")\
    #    .add_attribute(Browsable(False))
    #   .add_attribute(OpenTap.Display("Available Values", "Select which values are available for 'Selectable'.", "Selectable"))
    CANIDFilt = property(Int32, 0x6f8)\
        .add_attribute(OpenTap.Display("CANID to Receive", "", "Input", 0))

    CANIDMask = property(Int32, 0x000007FF)\
        .add_attribute(OpenTap.Display("CAN Mask ", "", "Input", 0.1))
    # CANExt
    CANExt = property(Boolean, False)\
        .add_attribute(OpenTap.Display("Extended ID", "", "Input", 0.3))
    CANTimeout = property(Double, 1.0)\
        .add_attribute(OpenTap.Display("CAN Timeout", "", "Input", 0.2))\


    
    CANID = property(Double, 1.0)\
        .add_attribute(OpenTap.Display("CAN ID Ftr", "", "Output", 1.0))\
        .add_attribute(OpenTap.Output())

    CANValue = property(String, "")\
        .add_attribute(OpenTap.Display("Value", "", "Output", 1.1))\
        .add_attribute(OpenTap.Output())
    CANData = property(List[Byte], None)\
        .add_attribute(OpenTap.Display("Data", "", "Output", 1.15))\
        .add_attribute(OpenTap.Output())

    CANTimeStamp = property(Double, 0)\
        .add_attribute(OpenTap.Display("TimeStamp", "", "Output", 1.2))\
        .add_attribute(OpenTap.Output())
    CANExt = property(Boolean, False)\
        .add_attribute(OpenTap.Display("Extended ID", "", "Output", 1.3))\
        .add_attribute(OpenTap.Output())

    CANFDMode = property(Boolean, False)\
        .add_attribute(OpenTap.Display("FD Mode", "", "Output", 1.4))\
        .add_attribute(OpenTap.Output())

    CheckLimits= property(Boolean, False)\
        .add_attribute(OpenTap.Display("Check Limits", "", "Limits", 2))
    MinimumValue = property(Double, -9999.0)\
        .add_attribute(OpenTap.Display("Minimum Value", "", "Limits", 2))\
        .add_attribute(OpenTap.EnabledIf("CheckLimits", True, HideIfDisabled = True))
    MaximumValue = property(Double, 9999.0)\
        .add_attribute(OpenTap.Display("Maximum Value", "", "Limits", 2))\
        .add_attribute(OpenTap.EnabledIf("CheckLimits", True, HideIfDisabled = True))
    

    ##@attribute(OpenTap.EnabledIf("FrequencyIsDefault", False, HideIfDisabled = True))
    def __init__(self):
        super().__init__() # The base class initializer must be invoked.
        self.log.Info("Init ReadCalibration message")
        self.Available = List[String]()
        """
        It might be better to set the filter here then just receive below"""
        # object types should be initialized in the constructor.
        self.Logging = OpenTap.Enabled[String]()
        # assign available cal from DUT characteristics list
        #self.Available = List[Int32]()
        #self.Available.Add(1)
        #self.Available.Add(2)
        #self.Available.Add(3)
        #self.Available.Add(4) # the backing data behaves as a python list in this case.
        
        # Add validation rules for the property. This makes it possible to tell the user about invalid property values.
        #self.Rules.Add(opentap.Rule("Frequency", lambda: self.Frequency >= 0, lambda: '{} Hz is an invalid value. Frequency must not be negative'.format(self.Frequency)))
        #self.Rules.Add(opentap.Rule("Frequency", lambda: self.Frequency <= 2e9, lambda: 'Frequency cannot be greater than {}.'.format(2e9)))
    
        
       

    def Run(self):
        super().Run() ## 3.0: Required for debugging to work. 
        
        # Write some log messages
#        self.log.Info("Info message")
#        self.log.Error("Error message")
#        self.log.Warning("Warning Message")
        #msg1 = Message(arbitration_id=0, is_extended_id=False)
        self.log.Info("Lets create some results from reading a CAN message: " )
        self.CANID = 0
        self.CANData = List[Byte]()
        try:        
            msg1 = self.Dut.ReadFilteredCAN(self.CANIDFilt, self.CANIDMask, self.CANExt, self.CANTimeout )
            
            self.log.Info("Read filt CAN Message returned {0:X} ", msg1)
            if ((msg1 is not None) and (msg1.arbitration_id != 0)):
                self.log.Debug("Not None Read filt CAN Message returned {0:X} ", msg1)
                self.CANID = msg1.arbitration_id  #.arbitration_id
                self.CANTimeStamp =  msg1.timestamp
                self.CANExt = msg1.is_extended_id
                self.CANFDMode = msg1.is_fd

                #self.CANValue = "0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x} 0x{:02x}"\
                #    .format( msg1.data[0], msg1.data[1], msg1.data[2], msg1.data[3], msg1.data[4], msg1.data[5], msg1.data[6], msg1.data[7] )
                #self.CANValue = '0x'+' 0x'.join(struct.pack('B',x).hex() for x in msg.data)
                self.CANValue = ' '.join(struct.pack('B',x).hex() for x in msg1.data)
                
                self.log.Info("CAN Message Data returned {0:X} ", msg1.data)
                for x in msg1.data:
                    self.CANData.Add(x)
                #self.CANData = list(msg1.data)
                self.UpgradeVerdict(OpenTap.Verdict.Pass)
            else:
                self.log.Info("No CAN Message Read")
                self.CANID = 0
                self.CANTimeStamp = 0
                self.CANValue =      ""
                self.UpgradeVerdict(OpenTap.Verdict.Fail)
                
            if (self.CheckLimits):
                if ((self.MinimumValue > self.CANID) | (self.MaximumValue < self.CANID)):
                    self.UpgradeVerdict(OpenTap.Verdict.Fail)

    #        self.log.Debug("Read Calibration {0} = {1}.",self.Calibration ,self.CANID)

            self.log.Debug("Read Filter CAN Read {0} {1}", self.CANID , msg1.data)
#        self.log.Debug("Calibration Value {0}.",   self.CANID)
#        self.log.Info("Run the reulst child steps.")
#        for step in self.EnabledChildSteps:
#            self.RunChildStep(step)
        

        # call method on the instrument.
#        self.log.Info("Measurement : {0} dBm", self.Instrument.do_measurement())

        
        # Set verdict
        except Exception as e:
            self.log.Error("Failed to read any CAN message")
            self.log.Debug(e)
            self.UpgradeVerdict(OpenTap.Verdict.Error)
        self.PublishResult("Read Filter CAN", ["CANID", "Value"], [  "0x{:08x}".format(self.CANID), self.CANValue]);

        