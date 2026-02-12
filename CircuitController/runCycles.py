from PowerSupply import PowerSupply
from kelctl import KELSerial
import time
import csv
import datetime


# save-slot(in which save-slot 1-10 the list will be saved in, int), 
# current_range(the limit up to which value the current can be set in Amps, 
# Lists are not restricted by limits set in settings, float), 
# discharge_current(current in Amps at which the battery will be discharged at, float), 
# cutoff_voltage(voltage in Volts at which test will stop, float), 
# cutoff_capacity(capacity in AH at which test will stop, float), 
# cutoff_time(time in minutes after which the test will stop, float)

class BatteryCycle:
    ps = None
    load = None

    halfCycle = 0
    newHalfCycle = True

    startTime = 0
    fileName = ""
    targetSaveFolder = "/Recordings/"

    csvData = []

    psUSBID = None
    eLoadUSB = None


    def __init__(self, eloadUSB, psUSBID):
        self.eLoadUSB = eloadUSB
        self.psUSBID = psUSBID


        self.ps = PowerSupply(self.psUSBID)

        self.load = KELSerial(self.eLoadUSB)
        self.load.__enter__()


    def charge(self):
        self.newHalfCycle = False

        #blocking
        self.ps.chargeConstantVoltage(4.2, 1.7, 68, True)
        # ps.chargeConstantCurrent(1.0, 4.2, 68, True)
        # ps.chargeConstantPower(4.0, 4.2, 1.7, 68, True)
        self.newHalfCycle = True

        self.halfCycle += 1

    def discharge(self):
        self.newHalfCycle = False

        # stats on the samsung inr18650-35e battery:
        # max charge voltage of 4.2V
        # standard current of 1.7A
        # recommended cut off of 68mA
        # nominal cell voltage of 3.6V
        # CC-CV charging system

        # The Samsung INR18650-35E has a nominal capacity of 3500mAh
        # and a minimum capacity of 3350mAh
        # The discharge cut-off voltage is 2.65V
        # It is designed for a maximum continuous discharge current of 8A

        #blocking
        # battList = BattList(1.7, 20.23, 2.5, 10, 30, 5)
        #1.5 cut off because of the decreased load voltage
        battList = BattList(1, 1.7, 1.7, 1.5, 3.35, 10)

        self.load.set_batt(battList)

        self.newHalfCycle = True

        self.halfCycle += 1

    def start(self):
        self.startTime = time.time()
        self.fileName = generateFileName()

        # with KELSerial(self.eLoadUSB) as load:
        #     print("Model: ", load.model)
        #     print("Status: ", load.status)

        startStamp()

        while (True):
            if (self.newHalfCycle):
                if (self.halfCycle % 2 == 1):
                    chargingThread = threading.Thread(target=charge, args=())
                    chargingThread.start()
                elif (self.halfCycle % 2 == 0):
                    chargingThread = threading.Thread(target=discharge, args=())
                    chargingThread.start()
            
            recordData()
            time.sleep(1)

        writeOut()
        exitAll()

    def generateFileName(self):
        return "logData" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    def startStamp(self):
        self.csvData.append(self.load.model, self.model.)
        self.csvData.append()
        self.csvData.append("time (s)", "current (A)", "voltage (V)", "power (W)", "State")

    def recordData(self):
        state = ""
        if (self.halfCycle % 2 == 1):
            state = "charging"
        else:
            state = "discharging"

        self.csvData.append(str(time.time()-self.startTime), 
                            self.load.measured_current,
                            self.load.measured_voltage,
                            self.load.measured_power,
                            state
                            )

    def writeOut(self):
        with open(self.targetSaveFolder + self.fileName, 'w') as csvFile:
            csvWriter = csv.writer(csvfile)
            csvwriter.writerows(self.csvData)

    def exitAll(self):  
        self.ps.setOutputOff()
        self.ps.closeConnection()

        self.load.__exit__(None, None, None)



cycle = BatteryCycle('/dev/ttyACM0', 'USB0::6833::3601::DP8D202700178::0::INSTR')
cycle.start()



    