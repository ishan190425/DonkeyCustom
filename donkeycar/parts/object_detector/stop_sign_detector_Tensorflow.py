import RPi.GPIO as GPIO

class StopSignDetector(object):
    '''
    Based on Tensorflow Object Detction API
    Jan 24, 2023
    @author:Ishan190425
    '''

    def __init__(self):
        self.pin = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin,GPIO.IN)
    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_stop_sign (self):
        if GPIO.input(self.pin):
                print("Found Stop Sign")
                return [0,0]
        return []
    
    def run(self,*inputs):
        return self.detect_stop_sign()