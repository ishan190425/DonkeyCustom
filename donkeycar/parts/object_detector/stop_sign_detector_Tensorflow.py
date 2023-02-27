import importlib.util
import glob
import sys
import argparse
import numpy as np
import os
import urllib.request
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
import pathlib
from docopt import docopt
import cv2
from tensorflow.keras.models import load_model
import pickle
from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelBinarizer
import time
import PIL
import tflite_runtime.interpreter as tflite
# Patch the location of gfile
tf.gfile = tf.io.gfile

# Enable Eager Execution for Tensorflow Version < 2
tf.compat.v1.enable_eager_execution()

# num_threads = 4
# os.environ["OMP_NUM_THREADS"] = "4"
# os.environ["TF_NUM_INTRAOP_THREADS"] = "4"
# os.environ["TF_NUM_INTEROP_THREADS"] = "4"

# tf.config.threading.set_inter_op_parallelism_threads(
#     num_threads
# )
# tf.config.threading.set_intra_op_parallelism_threads(
#     num_threads
# )
# tf.config.set_soft_device_placement(True)

class StopSignDetector(object):
    '''
    Based on Tensorflow Object Detction API
    Jan 24, 2023
    @author:Ishan190425
    '''

    def __init__(self, show_bounding_box, max_reverse_count=0, reverse_throttle=-0.5, debug=False, model_name='ssd_mobilenet_v2_coco_2018_03_29'):
        # MODEL_NAME = model_name
        # PATH_TO_MODEL_DIR = self.download_model(MODEL_NAME)
        # PATH_TO_SAVED_MODEL = PATH_TO_MODEL_DIR + "/saved_model"
        
        # LABEL_FILENAME = 'mscoco_label_map.pbtxt'
        # PATH_TO_LABELS = self.download_labels(LABEL_FILENAME)

        # self.category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS,
        #                                                             use_display_name=True)
        # self.model = load_model("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/model_bbox_regression_and_classification",custom_objects={'Functional':tf.keras.models.Model})
        self.lb = pickle.loads(open("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/lb.pickle", "rb").read())

        self.show_bounding_box = show_bounding_box
        self.STOP_SIGN_CLASS_ID = 13
        self.debug = debug

        # reverse throttle related
        self.max_reverse_count = max_reverse_count
        self.reverse_count = max_reverse_count
        self.reverse_throttle = reverse_throttle
        self.is_reversing = False
        self.output = None
        self.input = None
        self.model = None
    
    def build_model(self):
        vgg = VGG16(weights="imagenet",
                    include_top=False,
                    input_tensor=Input(shape=(120, 160, 3)))

        # freeze training any of the layers of VGGNet
        vgg.trainable = False

        # max-pooling is output of VGG, flattening it further
        flatten = vgg.output
        flatten = Flatten()(flatten)
        # 4 neurons correspond to 4 co-ords in output bbox
        softmaxHead = Dense(512, activation="relu")(flatten)
        softmaxHead = Dropout(0.5)(softmaxHead)
        softmaxHead = Dense(512, activation="relu")(softmaxHead)
        softmaxHead = Dropout(0.5)(softmaxHead)
        softmaxHead = Dense(len(self.lb.classes_), activation="softmax",
                            name="class_label")(softmaxHead)
        model = Model(
            inputs=vgg.input,
            outputs=(softmaxHead))
        INIT_LR = 1e-4
        NUM_EPOCHS = 10
        BATCH_SIZE = 16
        self.index = 0
        opt = Adam(INIT_LR)

        model.compile(loss = tf.keras.losses.categorical_crossentropy)
        model.load_weights("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/model_bbox_regression_and_classification_weights")
        model.save("model.h5")
        converter = tf.lite.TFLiteConverter.from_keras_model_file("model.h5")
        # converter.optimizations = [tf.lite.Optimize.DEFAULT]
        # converter.target_spec.supported_types = [tf.float16]
        tf_lite_model = converter.convert()
        with open("model.tflite","wb") as file:
            file.write(tf_lite_model)
        interperter = tf.lite.Interpreter(model_path = "model.tflite")
        interperter.allocate_tensors()
        input = interperter.get_input_details()[0]["index"]
        output = interperter.get_output_details()[0]["index"]
        self.input = input
        self.output = output
        self.model = interperter
        print("Built model!")


    # Download and extract model
    def download_model(self,model_name):
        if os.path.isdir("Tensorflow/models/{}".format(model_name)):
            print("Found model!")
            return "Tensorflow/models/{}".format(model_name)
        base_url = 'http://download.tensorflow.org/models/object_detection/'
        model_file = model_name + '.tar.gz'
        model_dir = tf.keras.utils.get_file(fname=model_name,
                                            origin=base_url + model_file,
                                            untar=True, cache_subdir="Tensorflow/models/{}".format(model_name))
        return str(model_dir)


    # Download labels file
    def download_labels(self,filename):
        if os.path.isdir("Tensorflow/Labels/{}".format(filename)):
            print("Found model!")
            return "Tensorflow/Labels/{}".format(filename)
        base_url = 'https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/data/'
        label_dir = tf.keras.utils.get_file(fname=filename,
                                            origin=base_url + filename,
                                            untar=False, cache_subdir="Tensorflow/Labels/{}".format(filename))
        label_dir = pathlib.Path(label_dir)
        return str(label_dir)
            
            
    def load_image_into_numpy_array(self,img):
        """Load an image from file into a numpy array.

        Puts image into numpy array to feed into tensorflow graph.
        Note that by convention we put it into a numpy array with shape
        (height, width, channels), where channels=3 for RGB.

        Args:
        path: the file path to the image

        Returns:
        uint8 numpy array with shape (img_height, img_width, 3)
        """
        return np.asarray(img)

    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_stop_sign (self, img_arr=None):
        if not os.path.exists("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/img.jpg"):
            time.sleep(0.1)
            self.detect_stop_sign()
        try:
            img_arr = PIL.Image.open("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/img.jpg")
        except:
            time.sleep(0.1)
            self.detect_stop_sign()
        try:
            image_np = (np.array(img_arr)) / 255.0 
        except:
            image_np = (np.array(img_arr)) / 255.0 
        #print("Loaded Image")
        image_np = np.expand_dims(image_np, axis=0).astype(np.float32)
        #print("Converted to Numpy")
        #print("input - {}".format(self.model.get_input_details()))
        self.model.set_tensor(self.input,image_np)
        #print("Set Tensor")
        labelPreds = self.model.get_tensor(self.output)
        #print("Got Tensor")
        # finding class label with highest pred. probability
        i = np.argmax(labelPreds, axis=1)
        label = self.lb.classes_[i][0]
        print(label)
        traffic_light_obj = label == "stop"
        value = None
        if traffic_light_obj or self.is_reversing:
            # Set the throttle to reverse within the max reverse count when detected the traffic light object
            if self.reverse_count < self.max_reverse_count:
                self.is_reversing = True
                self.reverse_count += 1
                value = self.reverse_throttle, img_arr
            else:
                self.is_reversing = False
                value = 0, img_arr
            print("Found Stop Sign")
            with open('/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/stop.pickle','wb') as file:
                pickle.dump(value,file)
        elif os.path.exists("'/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/stop.pickle'"):
            os.remove("'/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/stop.pickle'")
        time.sleep(0.1)
        self.detect_stop_sign()
        return traffic_light_obj

    

    def run(self, img_arr, throttle, debug=False):
        if img_arr is None:
            return throttle, img_arr
        self.index += 1
        if self.index % 60:
            return throttle, img_arr 
        traffic_light_obj = self.detect_stop_sign(img_arr)

        if traffic_light_obj or self.is_reversing:
            # Set the throttle to reverse within the max reverse count when detected the traffic light object
            if self.reverse_count < self.max_reverse_count:
                self.is_reversing = True
                self.reverse_count += 1
                return self.reverse_throttle, img_arr
            else:
                self.is_reversing = False
                return 0, img_arr
        else:
            self.is_reversing = False
            self.reverse_count = 0
            return throttle, img_arr

if __name__ == "__main__":
    Object = StopSignDetector(show_bounding_box=False)
    Object.build_model()
    Object.detect_stop_sign()

