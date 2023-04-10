import serial
import time
import requests
import subprocess
import os

class Sensor():
    def __init__(self) -> None:
        self.ser = serial.Serial("/dev/ttyACM0", 9600,timeout=1)
        self.ser.reset_input_buffer()
        with open("/home/pi/projects/donkeycar/donkeycar/parts/web_controller/templates/static/final.txt", "w+", encoding = "utf-8") as file:
                file.write("[Ultra1, Ultra2, Ultra3, Ultra4, ACx, ACy, ACz, GyroX, GyroY, GyroZ, TFLuna Distance]\n")
    def checkUpdate(self):
        if self.ser.in_waiting > 0:
            serialData = self.ser.readline().decode('utf-8').rstrip()
            serialData = serialData.split()
            data = []
            final =  []
            for s in serialData:
                try:
                    label,number = s.split(":")
                    data.append(float(number))
                    full = f"{label}:{number}"
                    final.append(full)
                except:
                    continue
            with open("/home/pi/projects/donkeycar/donkeycar/parts/web_controller/templates/static/output.txt", "w+", encoding = "utf-8") as file:
                file.write(str(data))
            with open("/home/pi/projects/donkeycar/donkeycar/parts/web_controller/templates/static/final.txt", "a+", encoding = "utf-8") as file:
                file.write(str(final) + "\n")
    def run(self):
        self.checkUpdate()
        