"""
 A basic example of how to use User Input.
"""
import operator
from System import String, Object, Double
import System.Threading
import OpenTap
from OpenTap import Display, Submit, Layout, LayoutMode
from opentap import *
from enum import Enum

# This adds a couple buttons when the user request is invoked. Click OK, or cancel...
class OkEnum(Enum):
    Ok = ("Ok", "Ok")
    Cancel = ("Cancel", "Cancel")

    def __str__(self):
        return self.value[0]
    def describe(self):
        return self.value[1]

# Notice, this class inherits from System.Object(see line 4), a .NET class, not the default python object class.
class FactoryInfoInput(Object):
   TestName = property(String, "").add_attribute(Display("Test Name", "Enter a Name for this test."))
   PartNumber = property(String, "").add_attribute(Display("Part Number", "Enter the PartNumber for this Unit."))
   SerialNumber = property(String, "").add_attribute(Display("Serial Number", "Enter DUT Serial Number."))
   Operator = property(String, "").add_attribute(Display("Operator Name", "Enter Operator Name."))
   Notes = property(String, "").add_attribute(Display("Test Notes", "Enter Notes for this test run."))
   Ok = property(OkEnum, OkEnum.Ok)\
        .add_attribute(Submit())\
        .add_attribute(Layout(LayoutMode.FullRow | LayoutMode.FloatBottom))
   def __init__(self):
      super().__init__()

@attribute(OpenTap.Display("Factory Data Test Info Step", "As step for Entering Factory Data Information input.", "OpenECU Steps"))
class FactoryInfoInputStep(TestStep):
   TestName = property(String, "")\
        .add_attribute(OpenTap.Display("Test Name", "Enter a Name for this test.", "Test Information",1.0))\
        .add_attribute(OpenTap.Output())
   PartNumber = property(String, "")\
        .add_attribute(OpenTap.Display("Part Number", "Enter the PartNumber for this Unit.", "Test Information",1.0))\
        .add_attribute(OpenTap.Output())
   SerialNumber = property(String, "")\
        .add_attribute(OpenTap.Display("Serial Number", "Enter DUT Serial Number.", "Test Information",1.1))\
        .add_attribute(OpenTap.Output())
   Operator = property(String, "")\
        .add_attribute(OpenTap.Display("Operator Name", "Enter Operator Name.", "Test Information",1.2))\
        .add_attribute(OpenTap.Output())
   Notes = property(String, "")\
        .add_attribute(OpenTap.Display("Test Notes", "Enter Notes for this test run.", "Test Information",1.3))\
        .add_attribute(OpenTap.Output())
   SerialHigh = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialHigh", "High 32-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialLow = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialLow", "Low 32-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte0 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte0", "first 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte1 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte1", "Second 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte2 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte2", "Third 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte3 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte3", "Fourth 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte4 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte4", "Fifth 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())
   SerialByte5 = property(Double, 1.0)\
          .add_attribute(OpenTap.Display("SerialByte5", "Sixth 8-bits of Serial Number", "Output", 0))\
          .add_attribute(OpenTap.Output())

   def __init__(self):
      super().__init__()
   def Run(self):
      super().Run()
      
      obj = FactoryInfoInput()
      # This should pop up a dialog asking the user to fill out the data in the object.
      obj.TestName = self.TestName
      obj.SerialNumber = self.SerialNumber
      obj.Operator = self.Operator
      obj.Notes = self.Notes
      OpenTap.UserInput.Request(obj)
      if (obj.Ok == OkEnum.Ok):
          self.TestName = obj.TestName
          self.SerialNumber = obj.SerialNumber
          self.Operator = obj.Operator
          self.Notes = obj.Notes
          self.SerialHigh = (int(self.SerialNumber) & 0xFFFF00000000) >> 32
          self.SerialLow = (int(self.SerialNumber) & 0x00000000FFFFFFFF) 
          self.SerialByte0 = (int(self.SerialNumber) & 0xFF0000000000) >> 40
          self.SerialByte1 = (int(self.SerialNumber) & 0x00FF00000000) >> 32
          self.SerialByte2 = (int(self.SerialNumber) & 0x0000FF000000) >> 24
          self.SerialByte3 = (int(self.SerialNumber) & 0x000000FF0000) >> 16
          self.SerialByte4 = (int(self.SerialNumber) & 0x00000000FF00) >> 8
          self.SerialByte5 = (int(self.SerialNumber) & 0x0000000000FF) 

      self.PublishResult("Test Information", [ "Signal", "Value"], ["Test Name", self.TestName ]);
      self.PublishResult("Test Information", [ "Signal",  "Value"], ["Serial Number",self.SerialNumber]);
      self.PublishResult("Test Information", [ "Signal",  "Value"], ["Operator",self.Operator]);
      self.PublishResult("Test Information", [ "Signal", "Value"], [ "Notes", self.Notes]);

      self.log.Info("Test Name: " + self.TestName )
      self.log.Info("Test DUT Serial Number: " + self.SerialNumber)
      self.log.Info("Test Operator: " + self.Operator )
      self.log.Info("Test Notes: " + self.Notes)

      #print(obj.Frequency)  
