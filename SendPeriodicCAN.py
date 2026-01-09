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
from System import Array, Double, Byte, Int32, String, Boolean, Int16 # Import types to reference for generic methods
from System.ComponentModel import Browsable # BrowsableAttribute can be used to hide things from the user.
#import System.Xml
#from System.Xml.Serialization import XmlIgnore
import can
from can.bus import BusState
from can import *

from .CANDut import CANDut
#from .CANSettings import CANSettings


# Here is how a test step plugin is defined: 

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("Send Periodic CAN ", "Send a CAN message from CAN DUT every CANPeriod seconds for CANDuration Seconds. (Python CAN)", "CAN Steps"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class SendPeriodCAN(TestStep): # Inheriting from opentap.TestStep causes it to be a test step plugin.
    # Add properties (name, value, C# type)
    
    Dut = property(CANDut, None).add_attribute(OpenTap.Display( "DUT", "The DUT to use in the step.", "Resources"))
    

    CANExt = property(Boolean, False)\
        .add_attribute(OpenTap.Display("Extended ID", "", "Input", 0.3))
    CANFDMode = property(Boolean, False)\
        .add_attribute(OpenTap.Display("FD Mode", "", "Input", 0.4))
    
#    CANTimeout = property(Double, 1.0)\
#        .add_attribute(OpenTap.Display("CAN Timeout", "", "Input", 0.4))
    CANID = property(Int32, 1)\
        .add_attribute(OpenTap.Display("CAN ID", "", "Input", 0.1))

    CANData = property(List[Byte],None)\
        .add_attribute(OpenTap.Display("Data", "", "Input", 0.2))
    CANPeriod = property(Double, 0.1)\
        .add_attribute(OpenTap.Display("Time Period ", "", "Input", 0.15))
    CANDuration = property(Double, 1)\
        .add_attribute(OpenTap.Display("Duration", "Duration to periodically send", "Input", 0.18))

    IncrementByte = property(Boolean, False)\
        .add_attribute(OpenTap.Display("Increment Byte", "Increment a byte in each message", "Increment", 2.0))
    ByteLocation = property(Byte, 1)\
        .add_attribute(OpenTap.Display("Byte to Increment", "Which byte should be incremented", "Increment", 2.1))
    Increment = property(Int16, 1)\
        .add_attribute(OpenTap.Display("Increment", "Amount to incremented each time", "Increment", 2.2))
    # Need to add rules to limit to +255 to -255

    ##@attribute(OpenTap.EnabledIf("FrequencyIsDefault", False, HideIfDisabled = True))
    def __init__(self):
        super().__init__() # The base class initializer must be invoked.
        self.log.Info("Init Send Periodic CAN message")

        
        # Add validation rules for the property. This makes it possible to tell the user about invalid property values.
        #self.Rules.Add(opentap.Rule("Frequency", lambda: self.Frequency >= 0, lambda: '{} Hz is an invalid value. Frequency must not be negative'.format(self.Frequency)))
        #self.Rules.Add(opentap.Rule("Frequency", lambda: self.Frequency <= 2e9, lambda: 'Frequency cannot be greater than {}.'.format(2e9)))
    
        
       

    def Run(self):
        super().Run() ## 3.0: Required for debugging to work. 
        
        # Write some log messages
        self.log.Info("Lets send a CAN message to ID {0}: every {1}s for {2}s with data {3:x} {4:x} {5:x} {6:x}", self.CANID, self.CANPeriod, self.CANDuration, self.CANData[0], self.CANData[1], self.CANData[2], self.CANData[3] )
        _dout = bytes(self.CANData)
        self.log.Debug("init dout = {0}", _dout)
        try:
            self.Dut.SendPeriodicCAN(self.CANID, _dout, self.CANExt, self.CANPeriod, self.CANDuration, self.IncrementByte, self.Increment, self.ByteLocation, self.CANFDMode)
        except Exception as e:
            self.log.Error("Periodic CAN message to ID {0} failed to", self.CANID)
            self.log.Debug(e)
            self.UpgradeVerdict(OpenTap.Verdict.Error)


        
        # Set verdict
#        self.UpgradeVerdict(OpenTap.Verdict.Pass)
        