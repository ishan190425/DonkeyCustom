import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Dropout, Flatten
import numpy as np
from tensorflow.keras.models import Model
from typing import Tuple, Dict, Union, List
import time
import PIL
import pygame
import pygame.camera
import RPi.GPIO as GPIO


class StopSignDetector(object):
    '''
    Based on Tensorflow Object Detction API
    Jan 24, 2023
    @author:Ishan190425
    '''
    def predict(self,image):
        # Load and preprocess the image
        image = np.expand_dims(image, axis=0)  # Add a batch dimension
        image = image / 255.0  # Normalize the image

        # Predict if the image contains a stop sign
        prediction = self.model.predict(image)

        return True if prediction[0][0] > 0.5 else False
    def core_cnn_layers(self, img_in, drop):
        x = tf.keras.layers.Conv2D(24, (5, 5), strides=(2, 2), activation='relu')(img_in)
        x = tf.keras.layers.Conv2D(32, (5, 5), strides=(2, 2), activation='relu')(x)
        x = tf.keras.layers.Conv2D(64, (5, 5), strides=(2, 2), activation='relu')(x)
        x = tf.keras.layers.Conv2D(64, (3, 3), strides=(1, 1), activation='relu')(x)
        x = tf.keras.layers.Conv2D(64, (3, 3), strides=(1, 1), activation='relu')(x)
        x = Flatten()(x)
        x = Dense(100, activation='relu')(x)
        x = Dropout(drop)(x)
        x = Dense(50, activation='relu')(x)
        x = Dropout(drop)(x)
        return x
    def default_n_linear(self, num_outputs, input_shape=(120, 160, 3)):
        drop = 0.2
        img_in = Input(shape=input_shape, name='img_in')
        x = self.core_cnn_layers(img_in, drop)

        outputs = []
        for i in range(num_outputs):
            outputs.append(
                Dense(1, activation='linear', name='n_outputs' + str(i))(x))

        model = Model(inputs=[img_in], outputs=outputs, name='linear')
        return model
    def load_model_weights(self, weights_path):
        self.model.load_weights(weights_path)
        return

    def __init__(self, show_bounding_box=False, max_reverse_count=0, reverse_throttle=-0.5, debug=False, model_name='ssd_mobilenet_v2_coco_2018_03_29'):
        input_shape = (120, 160, 3)
        num_outputs = 2

        self.model = self.default_n_linear(num_outputs, input_shape)
        self.model.compile(optimizer='adam', loss='mse')
        self.load_model_weights("weights.h5")
       
        pygame.init()
        pygame.camera.init()
        self.cam = pygame.camera.Camera("/dev/video0",(160,120))
        self.cam.start()
        
        self.pin = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin,GPIO.OUT)
        GPIO.output(self.pin,GPIO.LOW)
        
        self.start_time = time.time()

    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_stop_sign (self, img_arr=None):
        
        #screen = pygame.display.set_mode((160,120))
        seen = 0
        while True:
            image = self.cam.get_image()
            show_image = image
            image = pygame.surfarray.array3d(image)
            image = image.swapaxes(0,1)
            img_arr = image
            
            label = self.predict(img_arr)
            traffic_light_obj = label
            
            #screen.blit(show_image,(0,0))
            #pygame.display.flip()
            
            current_time = time.time()
            fps = 1.0 / (current_time-self.start_time)
            self.start_time = current_time
            
            if traffic_light_obj :
                GPIO.output(self.pin,GPIO.HIGH)
#                 print(f"Found stop sign - {seen} and fps is {fps}\n")
                seen += 1
            else:
                GPIO.output(self.pin,GPIO.LOW)
        #self.detect_stop_sign()
        return traffic_light_obj

    



if __name__ == "__main__":
    Object = StopSignDetector(show_bounding_box=False)
    Object.detect_stop_sign()
