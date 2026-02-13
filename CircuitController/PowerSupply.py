import pyvisa
import time
import threading

class PowerSupply:

    rm = None
    instrument = None

    isLimitProtectionOn = False
    isThreadRunning = False

    maxVoltage = 0
    maxCurrent = 0

    prevCurrent = 0
    prevVoltage = 0
    
    def __init__(self, dp800Address):
        #set dp800a address for future reference (none of now)
        self.dp800Address = dp800Address
        
        self.initializeConnection()
        # self.initializeConnection(dp800Address)



    #connection/channel config methods

    def initializeConnection(self):
        #initialize the VISA Resource Manager
        self.rm = pyvisa.ResourceManager()
        
        self.instrument = self.rm.open_resource(self.dp800Address)
        
        self.instrument.timeout = 5000 # 5 seconds
        
        # identify the instrument
        print("Connected to:", self.instrument.query("*IDN?"))

        # 5. Control the Power Supply
        # Select Channel 1 (DP811A has one channel, but it must be selected)
        # instrument.write(':INST CH1')
        
    
    # list all connected resources to find the USB instrument
    def getManagerResources(self):
        return self.rm.list_resources()
        
    def setOutputOn(self):
        self.instrument.write(':OUTP CH1,ON')
        
    def setOutputOff(self):
        self.instrument.write(':OUTP CH1,OFF')
        
    def closeConnection(self):
        self.instrument.close()
        
        
        
        
    # output current/voltage methods

    def setOutputVoltage(self, voltage):
        if (self.isLimitProtectionOn and voltage > self.maxVoltage):
            try:
                self.startErrorBeep()
                self.emergencyDisable()
            except:
                print("Device Disable Error")
                
            raise Exception("Voltage limit exceeded with " + str(voltage) + "V. Please set correct voltage with setMaxVoltageLimit()") 
        
        self.instrument.write(':APPL CH1,' + str(voltage) + ',' + str(self.prevCurrent))
        
        self.prevVoltage = voltage

    def setOutputAmperage(self, amps):
        if (self.isLimitProtectionOn and amps > self.maxCurrent):
            try:
                self.startErrorBeep()
                self.emergencyDisable()
            except:
                print("Device Disable Error")
                
            raise Exception("Amperage limit exceeded with " + str(amps) + "A. Please set correct amperage with setMaxAmperageLimit()") 
        
        self.instrument.write(':APPL CH1,' + str(self.prevVoltage) + ',' + str(amps))
        
        prevCurrent = amps
        
    def setVoltageAndAmps(self, voltage, amps):
        self.setOutputVoltage(voltage)
        self.setOutputAmperage(amps)
        
    def getOutputVoltage(self):
        return float(self.instrument.query(':MEAS:VOLT? CH1'))

    def getOutputAmperage(self):
        return float(self.instrument.query(':MEAS:CURR? CH1'))

    def getOutputResistance(self):
        ampsOut = float(self.getOutputAmperage())
        voltsOut = float(self.getOutputVoltage())
            
        return voltsOut/ampsOut

    def getOutputWatts(self):
        ampsOut = float(self.getOutputAmperage())
        voltsOut = float(self.getOutputVoltage())
            
        return voltsOut*ampsOut




    # max limit protection methods

    def setMaxVoltageLimit(self, voltage):
        self.maxVoltage = voltage
        
    def setMaxAmperageLimit(self, amps):
        self.maxCurrent = amps
        
    def getMaxVoltageLimit(self):
        return self.maxVoltage
        
    def getMaxAmperageLimit(self):
        return self.maxCurrent

    def enableLimitProtection(self):
        self.isLimitProtectionOn = True

    def disableLimitProtection(self):
        self.isLimitProtectionOn = True
        
        
        
        
    #charging methods

    #@params
    # constVoltage - set constant voltage for charge duration
    # maxCurrent - max current (A) for charging
    # milliCutOff - milliamp threshold to stop charging
    # headless - should charging status be printed
    def chargeConstantVoltage(self, constVoltage, maxCurrent, milliCutOff, headless):
        #simple CV charging system
        
        self.setVoltageAndAmps(constVoltage, maxCurrent)
        
        while True:
            time.sleep(1)
            
            if (self.getOutputAmperage() < milliCutOff/1000):
                break
            
            if (not headless):
                print("Voltage: " + str(self.getOutputVoltage()) + ", Amperage: " + str(self.getOutputAmperage()))
                
        self.setVoltageAndAmps(0, 0)
                
        # self.isThreadRunning = False


    #@params
    # constCurrent - set current to keep constant
    # maxVoltage - voltage will fluctuate to keep current constant. 'maxVoltage' is the highest possible limit for voltage in CC
    # milliCutOff - milliamp threshold to stop charging
    # headless - should charging status be printed
    def chargeConstantCurrent(self, constCurrent, maxVoltage, milliCutOff, headless):
        #simple CC charging system
        
        while True:
            time.sleep(1)
            
            newVoltage = self.getOutputResistance()*constCurrent
            
            #even if the input values lag, 
            isVoltageUnderLimit = maxVoltage > newVoltage
            
            if (isVoltageUnderLimit):
                self.setVoltageAndAmps(newVoltage, constCurrent)
                
            time.sleep(2)
            
            # In the event amperage is less than cut off threshold and voltage is over limit
            if ((self.getOutputAmperage() < milliCutOff/1000) and not isVoltageUnderLimit):
                break
            
            if (not headless):
                print("Voltage: " + str(self.getOutputVoltage()) + ", Amperage: " + str(self.getOutputAmperage()))
                
        self.setVoltageAndAmps(0, 0)
                
        # self.isThreadRunning = False
                
                
    #@params
    # constWattage - set wattage/power to keep constant
    # maxVoltage - voltage will fluctuate to keep current constant. 'maxVoltage' is the highest possible limit for voltage in CW
    # maxCurrent - maximum current
    # milliCutOff - milliamp reading after the 
    # headless - should charging status be printed
    def chargeConstantPower(self, constWattage, maxVoltage, maxCurrent, milliCutOff, headless):
        #simple CP charging system
        
        #initial voltage set to start off our loop
        self.setVoltageAndAmps(maxVoltage/4, constWattage/maxVoltage)
        
        while True:
            time.sleep(1)
            
            newVoltage = constWattage/self.getOutputAmperage()
            
            #even if the input values lag, 
            isVoltageUnderLimit = maxVoltage > newVoltage
            
            if (isVoltageUnderLimit):
                self.setVoltageAndAmps(newVoltage, maxCurrent)
                
            time.sleep(2)
            
            # In the event amperage is less than cut off threshold and voltage is over limit
            if ((self.getOutputAmperage() < milliCutOff/1000) and not isVoltageUnderLimit):
                break
            
            if (not headless):
                print("Voltage: " + str(self.getOutputVoltage()) + ", Amperage: " + str(self.getOutputAmperage()))
                
        self.setVoltageAndAmps(0, 0)
                
        # self.isThreadRunning = False
        

    #(DEPRECIATED)
    # Charge with specified type
    # @param
    # type - type of charging system
    #    type == "CV" -> constant voltage charging
    #    type == "CC" -> constant current charging
    #    type == "CP" -> constant power (wattage) charging
    # milli - cut off milliamp threshold for stopping the charger
    # def charge(self, type, milliCutOff, maxVoltage, maxCurrent):
        
    #     if (self.isThreadRunning):
    #         raise Exception("thread is currently running")
        
    #     switcher = {
    #     "CV": self.chargeConstantVoltage,
    #     "CC": self.chargeConstantCurrent,
    #     "CP": self.chargeConstantPower
    #     }

    #     result = switcher.get(type, lambda: "unknown")()
        
        
    #     if (result == "unknown"):
    #         raise Exception("Provided charging type doesn't match existing")


    #     chargingThread = threading.Thread(target=result, args=(maxVoltage, maxCurrent, milliCutOff, False))
    #     chargingThread.start()
        
    #     self.isThreadRunning = True
    
    #(DEPRECIATED)

        
    #extraneous methods

    def soundErrorBeep(self):
        self.instrument.write(':SYSTem:BEEPer:IMMediate')
        
    def zeroOutput(self):
        self.setOutputOn()
        self.setVoltageAndAmps(0, 0)
        
    def emergencyDisable(self):
        self.setVoltageAndAmps(0, 0)
        
        self.setOutputOff()
        
        self.closeConnection()