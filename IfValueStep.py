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

from enum import Enum


@attribute(OpenTap.Display("Operation to use for comparison", "Flow Control"))
class CompareOperation(Enum):
    Equals = ("Equals", "V0 equals V1")
    Different = ("Different", "V0 is different from V1")
    GreaterThan = ("Greater Than", "V0 is greater than V1")
    LessThan = ("Less Than", "V0 is less than V1")
    
    
    def __str__(self):
        return self.value[0]
    def describe(self):
        return self.value[1]

#Use the Display attribute to define how the test step should be presented to the user.
@attribute(OpenTap.Display("If Value", "Compare two values and run child if true.", "Flow Control"))
#AllowAnyChildAttribute is attribute that allows any child step to attached to this step
@attribute(OpenTap.AllowAnyChild())
class IfValueStepTest(TestStep):
    __clr_attribute__ = [Display("IfValue Step")]
#    __namespace__ = "TestModule"
        
    Value1 = property(Double, 0.0)\
        .add_attribute(OpenTap.Display("Value1", "First Value to compare.", "Inputs",1.0))
        
    Value2 = property(Double, 0.0)\
        .add_attribute(OpenTap.Display("Value2", "Second Value to compare.", "Inputs",1.2))
    CompOperator = property(CompareOperation, CompareOperation.Equals)\
        .add_attribute(OpenTap.Display("Comparison", "Comparison Operator.", "Inputs",1.1))
    def __init__(self):
        print("IfValueStepTestInit!")
        super().__init__()
    
        
    def Run(self):
        super().Run()   ####super(IfValueStepTest, self).Run()
        self.log.Debug("Value1: {0}", self.Value1)
        self.log.Debug("Value2: {0}", self.Value2)
        self.log.Info("Info message")
#        self.log.Error("Error message")
#        self.log.Warning("Warning Message")
        self.log.Debug("CompOperator is {0}", self.CompOperator)
        
        match self.CompOperator:
           case CompareOperation.Equals:
               if (self.Value1 == self.Value2):
#            self.Results = 1;
                    self.log.Debug("{0} is {1} Than {2}", self.Value1, self.CompOperator, self.Value2)
                    self.RunChildSteps(); # If step has child steps.
           case CompareOperation.Different:
               if (self.Value1 != self.Value2):
                   self.log.Debug("{0} is {1} Than {2}", self.Value1, self.CompOperator, self.Value2)
                   self.RunChildSteps(); # If step has child steps.
           case CompareOperation.GreaterThan:
               if (self.Value1 > self.Value2):
                   self.log.Debug("{0} is {1} Than {2}", self.Value1, self.CompOperator, self.Value2)
                   self.RunChildSteps(); # If step has child steps.
           case CompareOperation.LessThan:
               if (self.Value1 < self.Value2):
                   self.log.Debug("{0} is {1} Than {2}", self.Value1, self.CompOperator, self.Value2)
                   self.RunChildSteps(); # If step has child steps.
           case _:  # default
               if (self.Value1 == self.Value2):
                   self.log.Debug("{0} is {1} Than {2}", self.Value1, self.CompOperator, self.Value2)
                   self.RunChildSteps(); # If step has child steps.

        
            
