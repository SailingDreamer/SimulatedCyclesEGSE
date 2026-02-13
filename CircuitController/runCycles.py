from PowerSupply import PowerSupply
from kelctl import KELSerial
import time
import csv
import datetime
import threading
from kelctl import BattList
import sys

from pynput.keyboard import Key, Listener, KeyCode
from pynput import keyboard



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

    halfCycle = 1
    newHalfCycle = True

    startTime = 0
    fileName = ""
    targetSaveFolder = "Recordings/"

    csvData = []
    
    shouldEnd = False

    psUSBID = None
    eLoadUSB = None


    def __init__(self, eloadUSB, psUSBID):
        self.eLoadUSB = eloadUSB
        self.psUSBID = psUSBID

        self.load = KELSerial(self.eLoadUSB)
        # self.ps = PowerSupply(self.psUSBID)
        self.ps = PowerSupply(psUSBID)
        
        self.load.__enter__()
        
        #keyboard interrupt
        
        # with Listener(on_press=self.onKeyPressed) as listener:
        #     listener.join() 
        listener = keyboard.Listener(on_press=self.onKeyPressed)
        listener.start()
            
            
    def onKeyPressed(self, key):
        try:
            # Check if the pressed key is a character key (e.g., 'm')
            if key.char == 'q':
                self.shouldEnd = True
                
                print("Ending Battery Test Program")
                print("")
                print("-------------------------")
                print("TOTAL CYCLES" + str(int(self.halfCycle/2)))
                print("-------------------------")
                        
                #disable both external actors
                # self.load.input.off()
                # self.ps.zeroOutput()
                
                self.writeOut()
                self.exitAll()
                
                sys.exit()
                
        except AttributeError:
            print("Error with keyboard listener")


    def charge(self):
        print("Starting charge")
        
        self.newHalfCycle = False

        self.ps.setOutputOn()
        
        
        # Standard Charging Speed: The standard, recommended charging current for the 35E is 1,700mA (1.7A), 
        # which takes approximately 4 hours to reach a full charge.
        # Rapid Charging Speed: The maximum rapid charge current is 2,000mA (2A), 
        # which can reduce charging time to around 3 hours.
        # For Maximum Life: To prolong the battery's health, a charge current of 1,020mA (1A) is recommended. 
        
        #blocking
        self.ps.chargeConstantVoltage(4.2, 1.7, 68, False)
        # ps.chargeConstantCurrent(1.0, 4.2, 68, True)
        # ps.chargeConstantPower(4.0, 4.2, 1.7, 68, True)
        
        self.ps.zeroOutput()
        
        print("Battery fully charged. Switching power off.")
        
        # !Do not use the following if you don't have a diode or a limiter!
        # self.ps.setOutputOff()
        
        self.newHalfCycle = True
        

        self.halfCycle += 1

    def discharge(self):
        
        print("Starting discharge")
        
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
        # battList = BattList(1, 1.7, 1.7, 1.5, 3.35, 10)
        
        self.load.settings.voltage_limit = 5.0
        self.load.settings.current_limit = 3
        
        # self.load.set_batt(battList)
        self.load.current = 1.0
        time.sleep(2)
        
        self.load.input.on()
        
        #Note that althought the safe discharge voltage for the SamsungINR18650-35E is 2.5V,
        #the Eload pulls the actual voltage lower, so we choose 1.9 volts instead.
        
        while (self.load.measured_voltage > 1.7):
            print("Voltage: " + str(self.load.measured_voltage) + " V, Current: " + str(self.load.measured_current) + " A.")
            self.load.current = 2.0
            time.sleep(1)
            
        print("Voltage below discharge threshold. Switching off")
            
        self.load.input.off()

        self.newHalfCycle = True

        self.halfCycle += 1

    def start(self):
        self.startTime = time.time()
        self.fileName = self.generateFileName()

        # with KELSerial(self.eLoadUSB) as load:
        #     print("Model: ", load.model)
        #     print("Status: ", load.status)

        self.startStamp()

        while (True):
            if (self.newHalfCycle):
                if (self.halfCycle % 2 == 1):
                    chargingThread = threading.Thread(target=self.charge, args=())
                    chargingThread.start()
                elif (self.halfCycle % 2 == 0):
                    dischargingThread = threading.Thread(target=self.discharge, args=())
                    dischargingThread.start()
            
            self.recordData()
            
            if (self.shouldEnd):
                break
            
            time.sleep(1)
            
    def generateFileName(self):
        return "logData" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    def startStamp(self):
        self.csvData.append({self.load.model})
        self.csvData.append({})
        self.csvData.append({"time (s)", "current (A)", "voltage (V)", "power (W)", "state"})

    def recordData(self):
        state = ""
        if (self.halfCycle % 2 == 1):
            state = "charging"
        else:
            state = "discharging"

        self.csvData.append({str(time.time()-self.startTime), 
                            self.load.measured_current,
                            self.load.measured_voltage,
                            self.load.measured_power,
                            state
                            })

    def writeOut(self):
        with open(self.targetSaveFolder + self.fileName, 'w', encoding='utf-8', newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            csvWriter.writerows(self.csvData)

    def exitAll(self):  
        self.ps.zeroOutput()
        self.ps.closeConnection()
        
        
        self.load.current = 0.0
        self.load.input.off()

        self.load.__exit__(None, None, None)



cycle = BatteryCycle('/dev/ttyACM2', 'USB0::6833::3601::DP8D202700178::0::INSTR')
cycle.start()



    