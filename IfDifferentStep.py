""" Example of how a python class can be written. """
import sys
import opentap
from opentap import *
import clr
import OpenTap
from OpenTap import *
import math
from OpenTap import Log, AvailableValues, EnabledIf, Display, EmbedProperties
import System
from System import Array, Double, Byte, Int32, String, Boolean, Void
from System.ComponentModel import Browsable
import OpenTap.Python

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("If Different", "Compare two values and run child if true.", "Flow Control"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class IfDifferentStep(TestStep):
    __clr_attribute__ = [Display("If Values are Different Step")]
#    __namespace__ = "TestModule"
        
    Value1 = property(Double, 0.0)\
        .add_attribute(OpenTap.Display("Value1", "First Value to compare.", "Inputs",1.0))
        
    Value2 = property(Double, 0.0)\
        .add_attribute(OpenTap.Display("Value2", "Second Value to compare.", "Inputs",1.2))
    def __init__(self):
        print("IfValueStepTestInit!")
        super().__init__()
    
        
    def Run(self):
        super().Run()   ####super(IfValueStepTest, self).Run()
        self.log.Debug("Value1: {0}", self.Value1)
        self.log.Debug("Value2: {0}", self.Value2)
        self.log.Info("Info message")
        
        if (self.Value1 != self.Value2):
#            self.Results = 1;
            self.log.Debug("{0} is {1} Than {2}", self.Value1, "Different", self.Value2)
            self.RunChildSteps(); # If step has child steps.
