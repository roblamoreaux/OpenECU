""" Example of how a python class can be written. """
import sys
import time
import opentap
import clr
clr.AddReference("System.Collections")
from System.Collections.Generic import List
from opentap import *

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


# Here is how a test step plugin is defined: 

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("ReadMeasurement", "Read a Measurement from the OpenECU.", "OpenECU Steps"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class ReadMeasurement(TestStep): # Inheriting from opentap.TestStep causes it to be a test step plugin.
    # Add properties (name, value, C# type)
    
    Dut = property(ECUDut, None).add_attribute(OpenTap.Display( "DUT", "The DUT to use in the step.", "Resources"))
    
    Measurement = property(String, "")\
        .add_attribute(OpenTap.AvailableValues("Available"))\
        .add_attribute(OpenTap.Display("Measurement", "Measurement to read.", "Signal to Read",1))
    # This property is based on a C# list of items 'List<int>', List<double>, List<string> can also be used.
    #Available = Dut.Characteristic
    #Available = List[String]()
    Filter = property(String,"")\
        .add_attribute(OpenTap.Display("Measurement Filter", "", "Signal to Read", 0))
    PrevFilter = ""
    IsRunning = False

    Available = property(List[String], "")\
        .add_attribute(Browsable(True))\
       .add_attribute(OpenTap.Display("Available Values", "Select which values are available for 'Selectable'.", "Selectable"))
    
    MeasurementValue = property(Double, 1.0)\
        .add_attribute(OpenTap.Display("Value", "", "Output", 0))\
        .add_attribute(OpenTap.Output())

    CheckLimits= property(Boolean, False)\
        .add_attribute(OpenTap.Display("Check Limits", "", "Limits", 0))
    MinimumValue = property(Double, -99999.0)\
        .add_attribute(OpenTap.Display("Minimum Value", "", "Limits", 0))\
        .add_attribute(OpenTap.EnabledIf("CheckLimits", True, HideIfDisabled = True))
    MaximumValue = property(Double, 99999.0)\
        .add_attribute(OpenTap.Display("Maximum Value", "", "Limits", 0))\
        .add_attribute(OpenTap.EnabledIf("CheckLimits", True, HideIfDisabled = True))
    

    ##@attribute(OpenTap.EnabledIf("FrequencyIsDefault", False, HideIfDisabled = True))
    def __init__(self):
        super().__init__() # The base class initializer must be invoked.
        self.log.Info("Init ReadMeasurement message")
        self.Available = List[String]()
        self.IsRunning = False

        # object types should be initialized in the constructor.
        self.Logging = OpenTap.Enabled[String]()
        # assign available cal from DUT characteristics list
        # need to add a filter here to reduce number of selections
        #self.Available = self.Dut.Measurements 
        for x in self.Dut.Measurements:
            s = "{}".format(x)
            #self.log.Debug("current measurement = " + s)
            if self.is_InFilter(s):   #.Contains(self.Filter):
                self.Available.Add(s)
        self.log.Debug("updated self.available: {}".format(self.Available[0]))
        self.Rules.Add(Rule("Filter", lambda: self.RunRule() , lambda: 'Filter sepcified'))
#       
        
    
    def is_InFilter(self, s = ""):
        #self.log.Debug("is_InFilter s = " + s + "filter = " + self.Filter)
        if (self.Filter  != ""):
             if s.find(self.Filter) == -1: 
                return False # not in string
             else:
                 return True
             #s.Contains("{}".format(self.Filter))
        else:
             return True
       
    def RunRule(self):
        if (( not self.IsRunning ) and (self.Filter != self.PrevFilter)):
            #self.log.Debug("RM running Rule for filter '{0}' with previous filter '{1}'".format(self.Filter, self.PrevFilter))
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
        self.log.Debug("RMeasPPPPostRun")
        self.IsRunning = False
#        return super().PostPlanRun()

    def Run(self):
        super().Run() ## 3.0: Required for debugging to work. 
        try:
            # Write some log messages
            
            #self.log.Info("Lets create some results: " + self.Measurement)
            # call read Measurement function here
            # self.MeasurementValue = self.Dut.ReadMeasurement(self.Measurement);
            self.MeasurementValue = self.Dut.ReadMeasurement(self.Measurement);
            #self.log.Debug("Read Measurement {0}", cvalue )
    
            if (self.CheckLimits):
                if ((self.MinimumValue > self.MeasurementValue) | (self.MaximumValue < self.MeasurementValue)):
                    self.UpgradeVerdict(OpenTap.Verdict.Fail)
            

            self.log.Info("Read Measurement {0} = {1}.",self.Measurement ,self.MeasurementValue)
    #        self.log.Info("Read Measurement {0}", self.Measurement )
    
            
            # Set verdict
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as e:
            self.log.Error(" Failed to Open to read measurement " + self.Measurement)
            self.log.Debug(e)
            self.UpgradeVerdict(OpenTap.Verdict.Error)
        self.PublishResult("Read Measurement", ["Timestamp", "Measurement", "Value"], [time.asctime(), self.Measurement, self.MeasurementValue]);



        