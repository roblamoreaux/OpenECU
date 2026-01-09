"""
 A ECU example of how to define a DUT driver.
"""
from opentap import *
import OpenTap
from OpenTap import Log

from .ECUSettings import ECUSettings
from .XCPDut import XCPDut
try:
    from .CANDut import CANDut  # existing CCP path (adjust if different)
except Exception:
    CANDut = None

from pythonccp import ccp
from pythonccp.logger import Logger
from pythonccp.master import Master

import can
from can.bus import BusState
from can import *

MTA0 = 0
MTA1 = 1

#db = DB()
#@attribute(OpenTap.Display("ECU DUT", "Device Under Test", "Resources"))
#class ECUDut(object):

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
    A2LLoaded = False
    PrevA2LFileName = ""
    count = 0
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
        self.Settings = ECUSettings()
        self._backend = None
        self._a2l = None  # hook your existing A2L loader here

        self.A2LLoaded = False
        self.Measurements = List[String]()
        self.Characteristics = List[String]()
        self.Rules.Add(Rule("A2LFilePath", lambda: self.Checkfilename() != 0, lambda: 'Must Specify a file name for the A2LFile'))
        self.db = DB()
#        self.Measurements.Clear()
#        self.Characteristics.Clear()
        super(ECUDut, self).__init__() # The base class initializer must be invoked.
        self.HighPowerOn = False
        self.Name = "OpenECU DUT"
        self.count = 0

        self.log.Debug('Init OPENECU')
        
        #self.LoadA2L(self.A2LFilePath, initdb)
        #self.CloseA2LECU()
        #initdb.close()
        #self.log.Info(self.Name + " Closed")


        self.DTO = 0x6f8;
        self.CRO = 0x6f9;
        self.FDMode = False;
        self.BigEndian = False;
        
        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
        self.log.Info("******interfaces found (Init)")
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

    def _ensure_backend(self):
        if self.Settings.Protocol == "CCP":
            if CANDut is None:
                raise RuntimeError("CCP backend CANDut not available.")
            if self._backend is None or not isinstance(self._backend, CANDut):
                self._backend = CANDut(self.Settings)
        elif self.Settings.Protocol in ("XCP_CAN", "XCP_ETH"):
            if self._backend is None or not isinstance(self._backend, XCPDut):
                self._backend = XCPDut(self.Settings, a2l_db=self._a2l)

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
        self.log.Debug('GetCANInterfaces')
        interfaceconfigs = can.detect_available_configs(interfaces=["kvaser", "neovi", "pcan",  "canalystii", "virtual"])
        self.log.Info("******interfaces found (getCANInterfaces)")
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

    def connect(self):
        self._ensure_backend()
        self._backend.connect()

    def disconnect(self):
        if self._backend:
            self._backend.disconnect()

    # Calibration access; for XCP this uses upload/download by address unless you add symbol helpers
    def read_calibration(self, name_or_addr, length=None):
        if isinstance(name_or_addr, str):
            # If you add symbol helpers to XCPDut, call them here; otherwise expect addr/len
            raise NotImplementedError("Symbol-based read not implemented in XCP path.")
        return self._backend.read_by_addr(int(name_or_addr), int(length))

    def write_calibration(self, name_or_addr, value_or_bytes, length=None):
        if isinstance(name_or_addr, str):
            raise NotImplementedError("Symbol-based write not implemented in XCP path.")
        return self._backend.write_by_addr(int(name_or_addr), bytes(value_or_bytes))
           
    def is_test_running(self):
        """
        Checks if a test plan is currently running.
        """
        plan_run =  self.t.   self.is_test_running
        self.log.Debug("PlanRun State is = {0}".format( plan_run))
        return plan_run #is not None and not plan_run.IsFinished

    
        
    def Checkfilename(self):
        self.log.Debug('CheckFileName')
        #TestPlan plan = TestPlan.Current;

        # Check if the plan is currently running.
        if ((not self.A2LLoaded) or (self.PrevA2LFileName != self.A2LFilePath)):
        #if (True):
        #if (!plan.IsRunning):
        #if ( not self.is_test_running()):
            initdb = DB()
            A2LFile, _ext = os.path.splitext(self.A2LFilePath)
            self.GetCANInterfaces()
            _curdir = os.getcwd()
            _directory = os.path.dirname(self.A2LFilePath)
            self.log.Info("Filename is " + os.path.abspath(A2LFile))
            
            self.log.Debug('directory = {0} Filename = {1}'.format(_directory, A2LFile))
            if ((os.path.isfile(A2LFile + ".a2l") )):
                self.log.Info("A2L does exist dated {0}",os.path.getmtime(A2LFile + ".a2l"))
                self._a2ldbExists = False
                _a2lExists = True
                self.A2LFilePath = os.path.abspath(A2LFile)
            if ((os.path.isfile(A2LFile + ".a2ldb"))):
                self.log.Info("A2LDB does exist dated {0}",os.path.getmtime(A2LFile + ".a2ldb"))
                self._a2ldbExists = True 
                
                self.A2LFilePath = os.path.abspath(A2LFile)
            if ((os.path.isfile(A2LFile + ".a2ldb-journal"))):
                self.log.Debug("A2LDB-journal does exist (CheckFileName)")
                self._a2ldbExists = True
                self.A2LLoaded = True
    #            self.CloseA2LECU( initdb)
    #            self.db.close()
                #os.remove(A2LFile + ".a2ldb-journal")
                return -9
            self.log.Info("{0} {1}: LM={2}, LC={3}".format(_a2lExists, self._a2ldbExists,self.Measurements.Count,self.Characteristics.Count))
            #if ((_a2lExists) and (not _a2ldbExists ) and ((len(self.Measurements) == 0) or (len(self.Characteristics) == 0))):
            if ((self.A2LFilePath != self.oldA2LFile) and (_a2lExists) or ((self.Measurements.Count <= 1) or (self.Characteristics.Count <= 1))):
                self.LoadA2L(self.A2LFilePath, initdb)
                self.CloseA2LECU( initdb)
                self.A2LLoaded = True
        self.PrevA2LFileName = self.A2LFilePath
        
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
            self.log.Error("A2LDB-journal does exist (Open) Attempting Removal")
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
        #
        self.count += 1
        self.log.Info(" {0} Opened count: {1}".format(self.Name , self.count))

    def Close(self):
        """Called by TAP when the test plan ends.
            Add code to close CAN bus here
        """
        self.log.Info(self.Name + " Closing")
        #self.CloseA2LECU(self.db)
        self.log.Debug("Closing A2L Database (Close)")
        #self.db.close()
        self.master.close()
        #self.transport.close()
        self.count -= 1
        self.log.Info(" Closed {0} Opened count: {1}".format(self.Name , self.count))
        
        ######IF_DATA
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

        self.log.Info("Loading A2L DB")
        """ Code to read a2l and fill calibration and measurement lists here"""
#        self.db = DB()
        #self.log.Info("Opening A2L filename" + fileName)
        self.log.Info("Opening A2L directory" + directory)
        
        self.log.Info("Opening A2L" + A2LFile)
        self.log.Info(A2LFile + " Opening")
#### Needs error checking added including try  and catch since it is not graceful if the file is bad
        self._a2ldbExists = False
        try:
            if ((os.path.isfile(A2LFile + ".a2l") )):
                self.log.Info("A2L does exist modified {0}",os.path.getmtime(A2LFile + ".a2l"))
                self.log.Info("A2L does exist access dated {0}",os.path.getatime(A2LFile + ".a2l"))
            if ((os.path.isfile(A2LFile + ".a2ldb"))):
                self.log.Info("A2LDB does exist modified {0}",os.path.getmtime(A2LFile + ".a2ldb"))
                if((os.path.getmtime(A2LFile + ".a2ldb") < os.path.getmtime(A2LFile + ".a2l"))):
                    self.log.Info("A2L is newer so deleting A2LDB")
                    self._a2ldbExists = False
                    os.remove(A2LFile + ".a2ldb")
                else:
                    self.log.Info("A2LDB is newer")
                    self._a2ldbExists = True
                
            if ((os.path.isfile(A2LFile + ".a2ldb-journal"))):
                self.log.Error("A2LDB-journal does exist (LoadA2L) attempting removal")
                self._a2ldbExists = True
                os.remove(A2LFile + ".a2ldb-journal")
                return -9
            if ( self._a2ldbExists ):
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
        self.session.close()

    def CloseA2LECU(self, dbo):
        self.log.Debug("Closing A2L Database (CloseA2LECU)")
        try:
            #self.session.close()
            dbo.close()
        except Exception as e:
            self.log.Warning("No dbo to close")
            self.log.Debug(e)
        
        

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
        meas = Characteristic(self.session, _mstring)
#        self.log.Debug("Write Calibration datatype {0} ", meas.type)
#        self.log.Debug("Write Calibration compuMethod {0} ", meas.compuMethod.name)
#        self.log.Debug("Write Calibration address {0} ", meas.address)
#        self.log.Debug("Write Calibration byteorder {0} ", meas.byteOrder)
#        self.log.Debug("Write Cal datatype = {0}", meas.record_layout_components[0][1]['datatype'])
        #self.log.Debug("Read Measurement {0} ", meas)
        self.log.Debug("Write Calibration Address {0} ", meas.address)
        self.log.Debug("Write Calibration Type {0} ", meas.type)
        self.log.Debug("Write Calibration asam_dType {0} ", meas.fnc_asam_dtype)
        self.log.Debug("Write Calibration fnc_np_dtype {0} ", meas.fnc_np_dtype)
        self.log.Debug("Write cal size {0} ", meas.fnc_element_size)
        self.log.Debug("Write cal byteorder {0} ", meas.byteOrder)
        self.log.Debug("Write Calibration fnc_np_order {0} ", meas.fnc_np_order)
        self.log.Debug("Write Calibration name {0} ", meas.name)
        
        dtype = meas.fnc_asam_dtype  #meas.deposit.fncValues['datatype']
        size = meas.fnc_element_size  #self.datatypesize[dtype]
        #byteorder = "MSB_LAST"
#       
        compu = CompuMethod(self.session, meas.compuMethod.name)
        self.log.Debug("compu {0} ", compu)
        #dtype = meas.deposit.fncValues['datatype']
        #size = self.datatypesize[dtype]
        self.log.Debug("Write Calibration convtype {0} {1}, {2}",  compu.conversionType, dtype, size)
        self.log.Debug("Write Calibration compumethod data physical value {0} ", value)
        intvalue = compu.physical_to_int(value) 
        self.log.Debug("Write Calibration compumethod data word {0} type {1}, size {2}", intvalue, type(intvalue), sys.getsizeof(intvalue))
        
#       
        self.master.setMta(self.CRO,meas.address, meas.ecuAddressExtension, byteorder=meas.byteOrder)

        retvalue = self.master.dnload(canID=self.CRO, size=size, value=intvalue, datatype=dtype, byteorder=meas.byteOrder)
        self.log.Debug("Write Calibration retvalue {0} ", retvalue)
        self.master.disconnect(self.CRO, 0, self.Station)
        return retvalue.err


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
        meas = Measurement(self.session, _mstring)
        self.log.Debug("Write Measurement datatype {0} ", meas.datatype)
        self.log.Debug("Write Measurement compuMethod {0} ", meas.compuMethod.name)
        self.log.Debug("Write Measurement address {0} ", meas.ecuAddress)
        self.log.Debug("Write Measurement size {0} ", meas.datatype)
        self.log.Debug("Write Measurement byteorder {0} ", meas.byteOrder)
        compu = CompuMethod(self.session, meas.compuMethod.name)
#        self.log.Debug("Write Measurement convtype {0} ",  compu.conversionType)
#        self.log.Debug("Write Measurement compumethod data physical value {0} ", value)
        intvalue = compu.physical_to_int(value) 
#        self.log.Debug("Write Measurement compumethod data word {0} ", intvalue)
        #phyvalue = meas.compuMethod.int_to_physical(value)# compu.physical_to_int("Sinus") == 3
        # compu.int_to_physical(10) is None
        #self.log.Info("Read Measurement {0}", phyvalue)
#       
        self.master.setMta(self.CRO,meas.ecuAddress, meas.ecuAddressExtension, byteorder=meas.byteOrder)

        retvalue = self.master.dnload6(canID=self.CRO, value=intvalue, datatype=meas.datatype, byteorder=meas.byteOrder)
        self.log.Debug("Write Measurement retvalue {0} ", retvalue)
        if (retvalue.err ==1):
            self.log.Error("Write Measurement Error: {0} {1} ", cal, retvalue)
            
        self.master.disconnect(self.CRO, 0, self.Station)
        return retvalue.err

    def ReadMeasurement(self, cal = ""):
        """ enter function here """
#        self.log.Debug("Read Measurement  " + cal)
        ##### Add code to get value from CCCP here
        #get data size first
        # Upload data now
        self.log.Debug("dto={0}, CRO={1} measurement = {2}".format(self.DTO, self.CRO, cal))
        self.master.connect(self.CRO, 0, self.DTO)
        _mstring = cal;
        meas = Measurement(self.session, _mstring)
        self.log.Debug("Read Measurement datatype {0} ", meas.datatype)
        self.log.Debug("Read Measurement compuMethod {0} ", meas.compuMethod.name)
        size = self.datatypesize[meas.datatype]

        self.log.Debug("Read Measurement size {0} ", size)
        self.log.Debug("Read Measurement byteorder {0} ", meas.byteOrder)
        self.log.Debug("Read Measurement address {0} ", meas.ecuAddress)
        value = self.master.shortUp(self.CRO, self.DTO, size, meas.ecuAddress, meas.ecuAddressExtension, meas.datatype, meas.byteOrder)
        self.log.Debug("read returned value={0}xxx", value)
        
        compu = CompuMethod(self.session, meas.compuMethod.name)
        self.log.Debug("Read Measurement convtype {0} {1} ",  compu.conversionType, value)
        if (np.isnan(value) ): #value == float('NaN'):
            self.log.Warning("Read Measurement Error: {0} {1} ", cal, value)
            phyvalue = value
        elif (compu.conversionType == 'TAB_VERB'): #value == float('NaN'):
            self.log.Warning("Read Measurement enum: {0} {1} ", cal, value)
            phyvalue = value
        else:    
            phyvalue = compu.int_to_physical(value) 
        self.log.Debug("Read Measurement phyvalue {0} ", phyvalue)
        
        if isinstance(phyvalue, str):
            phyvalue = value
        elif (compu.conversionType == 'TAB_VERB'): #value == float('NaN'):
            phyvalue = value
        else: 
          phyvalue = meas.compuMethod.int_to_physical(value)# compu.physical_to_int("Sinus") == 3
        self.log.Debug("Read Measurement compumethod {0} ({1}) ", value, phyvalue)  # compu.int_to_physical(10) is None
        self.log.Debug("Read Measurement {0} {1}", cal, phyvalue)
        self.master.disconnect(self.CRO, 0, self.Station)
        return phyvalue

    #@method(Double)
    def ReadCalibration(self, cal = ""):
        """ enter function here """
#        self.log.Info("Read Calibration  " + cal)
        #get data size first
        # Upload data now
        self.master.connect(self.CRO, 0, self.DTO)
        meas = Characteristic(self.session, cal)
        self.log.Debug("Read Calibration Address {0} ", meas.address)
        self.log.Debug("Read Calibration Type {0} ", meas.type)
        self.log.Debug("Read Calibration asam_dType {0} ", meas.fnc_asam_dtype)
        self.log.Debug("Read Calibration fnc_np_dtype {0} ", meas.fnc_np_dtype)
        self.log.Debug("Read cal size {0} ", meas.fnc_element_size)
        self.log.Debug("Read cal byteorder {0} ", meas.byteOrder)
        self.log.Debug("Read Calibration fnc_np_order {0} ", meas.fnc_np_order)
        self.log.Debug("Read Calibration name {0} ", meas.name)
        
        dtype = meas.fnc_asam_dtype  #meas.deposit.fncValues['datatype']
        size = meas.fnc_element_size  #self.datatypesize[dtype]
        #byteorder = "MSB_LAST"
#        self.log.Debug("Read Calibration compuMethod {0} ", meas.compuMethod.name)
        value = self.master.shortUp(self.CRO, self.DTO, size, meas.address, meas.ecuAddressExtension, dtype, byteorder=meas.byteOrder)# meas.byteOrder)
        self.log.Debug("read returned {0}", value)
        
        ############# Probably should add code to properly convert the format here

        compu = CompuMethod(self.session, meas.compuMethod.name)
        self.log.Debug("Read Calibration convtype {0}; value {1}== {2} ",  compu.conversionType, value, float('NaN'))
        if np.isnan(value):   # value == float('NaN'):
            self.log.Warning("Read Calibration Error: {0} {1} ", cal, value)
            phyvalue = value
        else:    
            phyvalue = compu.int_to_physical(value) 
#            self.log.Debug("Read Calibration compumethod {0} {1} ", value, phyvalue)
            phyvalue = meas.compuMethod.int_to_physical(value)
        # compu.int_to_physical(10) is None
        self.master.disconnect(self.CRO, 0, self.Station)
        self.log.Debug("Read Calibration meas: {0} {1} ", cal, phyvalue)
        return phyvalue
        value = 999.0
#        self.log.Debug("Read Calibration {0} ", value)
        return value
