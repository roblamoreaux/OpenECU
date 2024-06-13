""" Example of how a python class can be written. """
from System.Collections.Generic import List
import sys
import opentap
import clr
clr.AddReference("System.Collections")
from opentap import *
import time

import OpenTap 
import math
from OpenTap import Log, AvailableValues

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


# Here is how a test step plugin is defined: 

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("WriteMeasurement", "Write a Measurement from the OpenECU.", "OpenECU Steps"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class WriteMeasurement(TestStep): # Inheriting from opentap.TestStep causes it to be a test step plugin.
    # Add properties (name, value, C# type)
    
    Dut = property(ECUDut, None).add_attribute(OpenTap.Display( "DUT", "The DUT to use in the step.", "Resources"))
    

    Measurement = property(String, "")\
        .add_attribute(OpenTap.AvailableValues("Available"))\
        .add_attribute(OpenTap.Display("Measurement", "Measurement to Write.", "Signal to Write",1))
    # This property is based on a C# list of items 'List<int>', List<double>, List<string> can also be used.
    
    Available = property(List[String], "")\
        .add_attribute(Browsable(False))\
        .add_attribute(OpenTap.Display("Available Values", "Select which values are available for 'Selectable'.", "Selectable"))
    Filter = property(String,"")\
        .add_attribute(OpenTap.Display("Measurement Filter", "", "Signal to Write", 0))

    PrevFilter = ""

    IsRunning = False

    MeasurementValue = property(Double, 1.0)\
        .add_attribute(OpenTap.Display("Value", "", "Input", 0))


    ##@attribute(OpenTap.EnabledIf("FrequencyIsDefault", False, HideIfDisabled = True))
    def __init__(self):
        super().__init__() # The base class initializer must be invoked.
        self.log.Info("Init WriteMeasurement message")
        self.Available = List[String]()
        self.IsRunning = False
        
        # object types should be initialized in the constructor.
        self.Logging = OpenTap.Enabled[String]()
        # assign available cal from DUT characteristics list
        for x in self.Dut.Measurements:
            s = "{}".format(x)
            #self.log.Debug("current measurement = " + s)
            if self.is_InFilter(s):   #.Contains(self.Filter):
                self.Available.Add(s)
        self.Rules.Add(Rule("Filter", lambda: self.RunRule() , lambda: 'Filter sepcified'))
    
    def is_InFilter(self, s = ""):
        #self.log.Debug("is_InFilter s = " + s + "filter = " + self.Filter)
        if (self.Filter  != ""):
             if s.find(self.Filter) == -1: 
                return False # not in string
             else:
                 return True
        else:
             return True
       
    def RunRule(self):
        if (( not self.IsRunning ) and (self.Filter != self.PrevFilter)):
            self.log.Debug("WMrunning Rule")
            self.Available.Clear()
            for x in self.Dut.Measurements:
                s = "{}".format(x)
                #self.log.Debug("current measurement = " + s)
                if self.is_InFilter(s):   #.Contains(self.Filter):
                        self.Available.Add(s)
                        #self.log.Debug("added")
        self.PrevFilter = self.Filter
            
        return True
                

    def PrePlanRun(self):
        self.IsRunning = True
        return super().PrePlanRun()

    def PostPlanRun(self):
        self.log.Debug("WMeasPostRun")
        self.IsRunning = False
        #return super().PostPlanRun()
       

    def Run(self):
        super().Run() ## 3.0: Required for debugging to work. 
        
        # Write some log messages
        
        self.log.Info("Lets create some results: " + self.Measurement)
        # call Write Measurement function here
        try:
            
                self.Dut.WriteMeasurement(self.Measurement, self.MeasurementValue);
                #self.log.Debug("Write Measurement {0}", cvalue )
                self.MeasurementValue =  self.MeasurementValue + 1.0;
        #        self.log.Info("Lets create some results: " + self.MeasurementValue)
                self.log.Info("Write Measurement {0} = {1}.",self.Measurement ,self.MeasurementValue)
        #        self.log.Debug("Write Measurement {0}", self.Measurement )
                
                # Set verdict
                self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as e:
            self.log.Error("Failed to write Measuement {0}", self.Measurement)
            self.log.Debug(e)
            self.UpgradeVerdict(OpenTap.Verdict.Error)
        self.PublishResult("Write Measurement", ["Timestamp", "Measurement", "Value"], [time.asctime(), self.Measurement, self.MeasurementValue]);

                