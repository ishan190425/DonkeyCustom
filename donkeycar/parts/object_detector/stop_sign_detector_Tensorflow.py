import numpy as np
import os
import urllib.request
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
import pathlib
import donkeycar as dk
from docopt import docopt
import cv2

# Patch the location of gfile
tf.gfile = tf.io.gfile

# Enable Eager Execution for Tensorflow Version < 2
tf.compat.v1.enable_eager_execution()
     

class StopSignDetector(object):
    '''
    Based on Tensorflow Object Detction API
    Jan 24, 2023
    @author:Ishan190425
    '''

    
    def __init__(self, show_bounding_box, max_reverse_count=0, reverse_throttle=-0.5, debug=False):
        self.cfg = dk.load_config(config_path='/home/pi/mycar/config.py')
        MODEL_NAME = self.cfg.STOP_SIGN_MODEL
        PATH_TO_MODEL_DIR = self.download_model(MODEL_NAME)
        PATH_TO_SAVED_MODEL = PATH_TO_MODEL_DIR + "/saved_model"
        
        LABEL_FILENAME = 'mscoco_label_map.pbtxt'
        PATH_TO_LABELS = self.download_labels(LABEL_FILENAME)

        self.category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS,
                                                                    use_display_name=True)
        self.model = tf.compat.v2.saved_model.load(PATH_TO_SAVED_MODEL)
        self.model = self.model.signatures['serving_default']

        self.show_bounding_box = self.cfg.STOP_SIGN_SHOW_BOUNDING_BOX
        self.STOP_SIGN_CLASS_ID = 13
        self.debug = debug

        # reverse throttle related
        self.max_reverse_count = max_reverse_count
        self.reverse_count = max_reverse_count
        self.reverse_throttle = reverse_throttle
        self.is_reversing = False

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
        return np.array(img)

    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_stop_sign (self, img_arr):

        image_np = self.load_image_into_numpy_array(img_arr)

        # Things to try:
        # Flip horizontally
        # image_np = np.fliplr(image_np).copy()

        # Convert image to grayscale
        # image_np = np.tile(
        #     np.mean(image_np, 2, keepdims=True), (1, 1, 3)).astype(np.uint8)

        # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
        input_tensor = tf.convert_to_tensor(image_np)
        # The model expects a batch of images, so add an axis with `tf.newaxis`.
        input_tensor = input_tensor[tf.newaxis, ...]
    
        output_dict = self.model(input_tensor)
        
        # Convert to numpy arrays, and take index [0] to remove the batch dimension.
        # We're only interested in the first num_detections.
        num_detections = int(output_dict.pop('num_detections'))
        output_dict = {key: value[0, :num_detections].numpy()
                       for key, value in output_dict.items()}
        # All outputs are batches tensors.

        output_dict['num_detections'] = num_detections

        # detection_classes should be ints.
        output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
        
        
        image_np_with_detections = image_np.copy()
        traffic_light_obj = False
        
        if self.STOP_SIGN_CLASS_ID in output_dict['detection_classes']:
            print("Found stop sign!")
            traffic_light_obj = True
            if self.show_bounding_box:
                print("Showing stop sign!")
                viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    output_dict['detection_boxes'],
                    output_dict['detection_classes'],
                    output_dict['detection_scores'],
                    self.category_index,
                    instance_masks=output_dict.get('detection_masks_reframed', None),
                    use_normalized_coordinates=True,
                    line_thickness=8)

        cv2.imshow("Stop Sign", image_np_with_detections)
        
        return traffic_light_obj

    

    def run(self, img_arr, throttle, debug=False):
        if img_arr is None:
            return throttle, img_arr

        # Detect traffic light object
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
