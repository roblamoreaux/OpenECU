"""
 A basic example of how to use User Input.
"""
#import Revision
import System
from System import Array, Double, Byte, Int32, String, Boolean, Object # Import types to reference for generic methods
from System.ComponentModel import Browsable # BrowsableAttribute can be used to hide things from the user.
import System.Threading
import os

import OpenTap
from OpenTap import Display, Submit, Layout, LayoutMode, FilePathAttribute, FilePath
from opentap import *
from enum import Enum
from datetime import datetime, date

# Get current datetime and date

# This adds a couple buttons when the user request is invoked. Click OK, or cancel...
class OkEnum(Enum):
    Ok = ("Ok", "Ok")
    Cancel = ("Cancel", "Cancel")

    def __str__(self):
        return self.value[0]
    def describe(self):
        return self.value[1]

# Notice, this class inherits from System.Object(see line 4), a .NET class, not the default python object class.
class PrintLabel(Object):
   PartName = property(String, "").add_attribute(Display("Model Name", "Enter the model Name for."))
   PartNumber = property(String, "").add_attribute(Display("Part Number", "Enter the Base PartNumber for this Unit."))
   SerialNumber = property(String, "").add_attribute(Display("Serial Number", "Enter DUT Serial Number."))
   Revision = property(String, "").add_attribute(Display("Revision", "Enter Revision Number."))
   ModLevel = property(String, "").add_attribute(Display("ModLevel", "Enter ModLevel for Unit."))
   Variant = property(String, "").add_attribute(Display("Variant", "Enter Variant for Unit."))
   Ok = property(OkEnum, OkEnum.Ok)\
        .add_attribute(Submit())\
        .add_attribute(Layout(LayoutMode.FullRow | LayoutMode.FloatBottom))
   def __init__(self):
      super().__init__()

@attribute(OpenTap.Display("Print Label Step", "Output datafile to print label .", "OpenECU Steps"))
class PrintLabelStep(TestStep):
   PartName = property(String, "")\
        .add_attribute(OpenTap.Display("Model Name", "Enter the Name for this Part.", "DUT Information",1.0))\
        .add_attribute(OpenTap.Output())
   PartNumber = property(String, "")\
        .add_attribute(OpenTap.Display("Part Number", "Enter the PartNumber for this Unit.", "DUT Information",1.0))\
        .add_attribute(OpenTap.Output())
   SerialNumber = property(String, "")\
        .add_attribute(OpenTap.Display("Serial Number", "Enter DUT Serial Number.", "DUT Information",1.1))\
        .add_attribute(OpenTap.Output())
   Revision = property(String, "00")\
        .add_attribute(OpenTap.Display("Revision Number", "Enter Revision Number.", "DUT Information",1.2))\
        .add_attribute(OpenTap.Output())
   ModLevel = property(String, "00")\
        .add_attribute(OpenTap.Display("Mod Level", "Enter ModLevel for this DUT.", "DUT Information",1.3))\
        .add_attribute(OpenTap.Output())
   Variant = property(String, "000")\
        .add_attribute(OpenTap.Display("Variant", "Enter Variant of this DUT.", "DUT Information",1.4))\
        .add_attribute(OpenTap.Output())
   CustomerPN = property(String, "")\
        .add_attribute(OpenTap.Display("Customer Part #", "Enter Customer part Number of this DUT.", "Customer Data",2.0))\
        .add_attribute(OpenTap.Output())
   CustomerText1 = property(String, "")\
        .add_attribute(OpenTap.Display("Customer Text 1", "Enter Customer Text Field 1", "Customer Data",2.1))\
        .add_attribute(OpenTap.Output())
   CustomerText2 = property(String, "")\
        .add_attribute(OpenTap.Display("Customer Text 2", "Enter Customer Text Field 2", "Customer Data",2.2))\
        .add_attribute(OpenTap.Output())
   Bitmap1FilePath = property(String, "")\
        .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Open, "bmp"))\
        .add_attribute(OpenTap.Display("Bitmap1 Path", "Enter the path to the Bitmap file.", "Customer Data",2.4))\
        .add_attribute(OpenTap.Output())
   Bitmap2FilePath = property(String, "")\
        .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Open, "bmp"))\
        .add_attribute(OpenTap.Display("Bitmap2 Path", "Enter the path to the Bitmap file.", "Customer Data",2.5))\
        .add_attribute(OpenTap.Output())
   Bitmap3FilePath = property(String, "")\
        .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Open, "bmp"))\
        .add_attribute(OpenTap.Display("Bitmap3 Path", "Enter the path to the Bitmap file.", "Customer Data",2.6))\
        .add_attribute(OpenTap.Output())
   LabelFilePath = property(String, None)\
        .add_attribute(FilePath(FilePathAttribute.BehaviorChoice.Save, "Text Files (*.txt)| All Files |*.*"))\
        .add_attribute(OpenTap.Display("File Path", "Enter the path to the print file.", "Options",3.0))\
        .add_attribute(OpenTap.Output())
   CheckData= property(Boolean, False)\
        .add_attribute(OpenTap.Display("Prompt?", "Prompt Before Printing", "Options", 3.1))

   def __init__(self):
      super().__init__()
   def Run(self):
      super().Run()
      now = datetime.now()
      today = date.today()
      todaystr = today.strftime('%d %b %Y')

      if (self.CheckData):
        obj = PrintLabel()
        self.LabelFilePath = os.path.abspath(self.LabelFilePath)
        # This should pop up a dialog asking the user to fill out the data in the object.
        obj.PartName = self.PartName
        obj.PartNumber = self.PartNumber
        obj.Variant = self.Variant
        obj.SerialNumber = self.SerialNumber
        obj.Revision = self.Revision
        obj.ModLevel = self.ModLevel
        OpenTap.UserInput.Request(obj)
        if (obj.Ok == OkEnum.Ok):
            self.PartNumber = obj.PartNumber
            self.PartName = obj.PartName
            self.Variant = obj.Variant
            #self.PartName = obj.PartName
            self.SerialNumber = obj.SerialNumber
            self.Revision = obj.Revision
            self.ModLevel = obj.ModLevel
      with open(self.LabelFilePath, 'w') as f: 
         f.write('Date	SN	PN	Rev	Mod	Opt	Model	Variant	Bitmap1	Bitmap2	Bitmap3	CustomerPN	CustomText1	CustomText2'+'\n' ) # should change this to a parameter called header
         f.write(todaystr +'\t') # need to insert date stamp here
         f.write(self.SerialNumber +'\t')
         f.write(self.PartNumber +'\t')
         f.write(self.Revision +'\t')
         f.write(self.ModLevel +'\t')
         f.write(self.Variant +'\t')
         f.write(self.PartName +'\t')
         f.write(os.path.abspath(self.Bitmap1FilePath) +'\t')   # do we needs this - can it be inthe header parameter?
         f.write(os.path.abspath(self.Bitmap2FilePath) +'\t')   # do we needs this - can it be inthe header parameter?
         f.write(os.path.abspath(self.Bitmap3FilePath) +'\t')   # do we needs this - can it be inthe header parameter?
         f.write(self.CustomerPN +'\t')
         f.write(self.CustomerText1 +'\t')
         f.write(self.CustomerText2 +'\t')
         f.write('\n')
      self.PublishResult("Test Information", [ "Signal", "Value"], ["Test Name", self.PartName ]);
      self.PublishResult("Test Information", [ "Signal",  "Value"], ["Serial Number",self.SerialNumber]);
      self.PublishResult("Test Information", [ "Signal",  "Value"], ["Revision",self.Revision]);
      self.PublishResult("Test Information", [ "Signal", "Value"], [ "ModLevel", self.ModLevel]);

      self.log.Info("Test Name: " + self.PartName )
      self.log.Info("Test DUT Serial Number: " + self.SerialNumber)
      self.log.Info("Test Revision: " + self.Revision )
      self.log.Info("Test ModLevel: " + self.ModLevel)

      #print(obj.Frequency)  
