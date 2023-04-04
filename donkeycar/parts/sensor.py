import serial
import time
import requests
import subprocess

class Sensor():
    def __init__(self) -> None:
        self.ser = serial.Serial("/dev/ttyACM0", 9600,timeout=1)
        self.ser.reset_input_buffer()
    def checkUpdate(self):
        if self.ser.in_waiting > 0:
            serialData = self.ser.readline().decode('utf-8').rstrip()
            serialData = serialData.split()
            i =0
            for s in serialData:
                try:
                    if(i < 4):
                        serialData[i] = int(s[3:])
                    else:
                        if(s[0].isalpha() and i>=4):
                            serialData.remove(s)
                            serialData[i] = int(serialData[i])
                    i+=1
                except:
                    continue
            print(serialData)
            with open("donkeycar/parts/web_controller/templates/output.txt", "w+", encoding = "utf-8") as file:
                file.write(str(serialData))
    def run(self,inputs):
        self.checkUpdate()
        

    