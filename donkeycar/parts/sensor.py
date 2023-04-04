import serial
import time
import requests
import subprocess
from flask import Flask, render_template
app = Flask(__name__)

ser = serial.Serial("/dev/ttyACM0", 9600,timeout=1)
ser.reset_input_buffer()
while True:
    if ser.in_waiting > 0:
        serialData = ser.readline().decode('utf-8').rstrip()
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
        with open("/home/pi/projects/donkeycar/donkeycar/parts/web_controller/templates/static/output.txt", "w+", encoding = "utf-8") as file:
            file.write(str(serialData))

    