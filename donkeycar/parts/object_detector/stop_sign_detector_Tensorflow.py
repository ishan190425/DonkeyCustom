import importlib.util
import glob
import sys
import argparse
import numpy as np
import os
import urllib.request
import numpy as np
import tensorflow.lite as tf
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

    def __init__(self, show_bounding_box, max_reverse_count=0, reverse_throttle=-0.5, debug=False, model_name='ssd_mobilenet_v2_coco_2018_03_29'):
        MODEL_NAME = model_name
        PATH_TO_MODEL_DIR = self.download_model(MODEL_NAME)
        PATH_TO_SAVED_MODEL = PATH_TO_MODEL_DIR + "/saved_model"
        
        LABEL_FILENAME = 'mscoco_label_map.pbtxt'
        PATH_TO_LABELS = self.download_labels(LABEL_FILENAME)

        self.category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS,
                                                                    use_display_name=True)
        self.model = tf.compat.v2.saved_model.load(PATH_TO_SAVED_MODEL)
        self.model = self.model.signatures['serving_default']

        self.show_bounding_box = show_bounding_box
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


# ######## Webcam Object Detection Using Tensorflow-trained Classifier #########
# #
# # Author: Evan Juras
# # Date: 11/11/22
# # Description:
# # This program uses a TensorFlow Lite object detection model to perform object
# # detection on an image or a folder full of images. It draws boxes and scores
# # around the objects of interest in each image.
# #
# # This code is based off the TensorFlow Lite image classification example at:
# # https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py
# #
# # I added my own method of drawing boxes and labels using OpenCV.
# # Import packages


# # Parse user inputs
# MODEL_NAME = args.modeldir
# GRAPH_NAME = args.graph
# LABELMAP_NAME = args.labels

# min_conf_threshold = float(args.threshold)
# use_TPU = args.edgetpu

# save_results = args.save_results  # Defaults to False
# show_results = args.noshow_results  # Defaults to True

# IM_NAME = args.image
# IM_DIR = args.imagedir

# # If both an image AND a folder are specified, throw an error
# if (IM_NAME and IM_DIR):
#     print('Error! Please only use the --image argument or the --imagedir argument, not both. Issue "python TFLite_detection_image.py -h" for help.')
#     sys.exit()

# # If neither an image or a folder are specified, default to using 'test1.jpg' for image name
# if (not IM_NAME and not IM_DIR):
#     IM_NAME = 'test1.jpg'

# # Import TensorFlow libraries
# # If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
# # If using Coral Edge TPU, import the load_delegate library
# pkg = importlib.util.find_spec('tflite_runtime')
# if pkg:
#     from tflite_runtime.interpreter import Interpreter
#     if use_TPU:
#         from tflite_runtime.interpreter import load_delegate
# else:
#     from tensorflow.lite.python.interpreter import Interpreter
#     if use_TPU:
#         from tensorflow.lite.python.interpreter import load_delegate



# # Get path to current working directory
# CWD_PATH = os.getcwd()

# # Define path to images and grab all image filenames
# if IM_DIR:
#     PATH_TO_IMAGES = os.path.join(CWD_PATH, IM_DIR)
#     images = glob.glob(PATH_TO_IMAGES + '/*.jpg') + glob.glob(PATH_TO_IMAGES +
#                                                               '/*.png') + glob.glob(PATH_TO_IMAGES + '/*.bmp')
#     if save_results:
#         RESULTS_DIR = IM_DIR + '_results'

# elif IM_NAME:
#     PATH_TO_IMAGES = os.path.join(CWD_PATH, IM_NAME)
#     images = glob.glob(PATH_TO_IMAGES)
#     if save_results:
#         RESULTS_DIR = 'results'

# # Create results directory if user wants to save results
# if save_results:
#     RESULTS_PATH = os.path.join(CWD_PATH, RESULTS_DIR)
#     if not os.path.exists(RESULTS_PATH):
#         os.makedirs(RESULTS_PATH)

# # Path to .tflite file, which contains the model that is used for object detection
# PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, GRAPH_NAME)

# # Path to label map file
# PATH_TO_LABELS = os.path.join(CWD_PATH, MODEL_NAME, LABELMAP_NAME)

# # Load the label map
# with open(PATH_TO_LABELS, 'r') as f:
#     labels = [line.strip() for line in f.readlines()]

# # Have to do a weird fix for label map if using the COCO "starter model" from
# # https://www.tensorflow.org/lite/models/object_detection/overview
# # First label is '???', which has to be removed.
# if labels[0] == '???':
#     del(labels[0])

# # Load the Tensorflow Lite model.
# # If using Edge TPU, use special load_delegate argument
# if use_TPU:
#     interpreter = Interpreter(model_path=PATH_TO_CKPT,
#                               experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
#     print(PATH_TO_CKPT)
# else:
#     interpreter = Interpreter(model_path=PATH_TO_CKPT)

# interpreter.allocate_tensors()

# # Get model details
# input_details = interpreter.get_input_details()
# output_details = interpreter.get_output_details()
# height = input_details[0]['shape'][1]
# width = input_details[0]['shape'][2]

# floating_model = (input_details[0]['dtype'] == np.float32)

# input_mean = 127.5
# input_std = 127.5

# # Check output layer name to determine if this model was created with TF2 or TF1,
# # because outputs are ordered differently for TF2 and TF1 models
# outname = output_details[0]['name']

# if ('StatefulPartitionedCall' in outname):  # This is a TF2 model
#     boxes_idx, classes_idx, scores_idx = 1, 3, 0
# else:  # This is a TF1 model
#     boxes_idx, classes_idx, scores_idx = 0, 1, 2

# # Loop over every image and perform detection
# for image_path in images:

#     # Load image and resize to expected shape [1xHxWx3]
#     image = cv2.imread(image_path)
#     image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     imH, imW, _ = image.shape
#     image_resized = cv2.resize(image_rgb, (width, height))
#     input_data = np.expand_dims(image_resized, axis=0)

#     # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
#     if floating_model:
#         input_data = (np.float32(input_data) - input_mean) / input_std

#     # Perform the actual detection by running the model with the image as input
#     interpreter.set_tensor(input_details[0]['index'], input_data)
#     interpreter.invoke()

#     # Retrieve detection results
#     boxes = interpreter.get_tensor(output_details[boxes_idx]['index'])[
#         0]  # Bounding box coordinates of detected objects
#     classes = interpreter.get_tensor(output_details[classes_idx]['index'])[
#         0]  # Class index of detected objects
#     scores = interpreter.get_tensor(output_details[scores_idx]['index'])[
#         0]  # Confidence of detected objects

#     detections = []

#     # Loop over all detections and draw detection box if confidence is above minimum threshold
#     for i in range(len(scores)):
#         if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):

#             # Get bounding box coordinates and draw box
#             # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
#             ymin = int(max(1, (boxes[i][0] * imH)))
#             xmin = int(max(1, (boxes[i][1] * imW)))
#             ymax = int(min(imH, (boxes[i][2] * imH)))
#             xmax = int(min(imW, (boxes[i][3] * imW)))

#             cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

#             # Draw label
#             # Look up object name from "labels" array using class index
#             object_name = labels[int(classes[i])]
#             label = '%s: %d%%' % (object_name, int(
#                 scores[i]*100))  # Example: 'person: 72%'
#             labelSize, baseLine = cv2.getTextSize(
#                 label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
#             # Make sure not to draw label too close to top of window
#             label_ymin = max(ymin, labelSize[1] + 10)
#             # Draw white box to put label text in
#             cv2.rectangle(image, (xmin, label_ymin-labelSize[1]-10), (
#                 xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED)
#             cv2.putText(image, label, (xmin, label_ymin-7),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)  # Draw label text

#             detections.append([object_name, scores[i], xmin, ymin, xmax, ymax])

#     # All the results have been drawn on the image, now display the image
#     if show_results:
#         cv2.imshow('Object detector', image)

#         # Press any key to continue to next image, or press 'q' to quit
#         if cv2.waitKey(0) == ord('q'):
#             break

#     # Save the labeled image to results folder if desired
#     if save_results:

#         # Get filenames and paths
#         image_fn = os.path.basename(image_path)
#         image_savepath = os.path.join(CWD_PATH, RESULTS_DIR, image_fn)

#         base_fn, ext = os.path.splitext(image_fn)
#         txt_result_fn = base_fn + '.txt'
#         txt_savepath = os.path.join(CWD_PATH, RESULTS_DIR, txt_result_fn)

#         # Save image
#         cv2.imwrite(image_savepath, image)

#         # Write results to text file
#         # (Using format defined by https://github.com/Cartucho/mAP, which will make it easy to calculate mAP)
#         with open(txt_savepath, 'w') as f:
#             for detection in detections:
#                 f.write('%s %.4f %d %d %d %d\n' % (
#                     detection[0], detection[1], detection[2], detection[3], detection[4], detection[5]))

# # Clean up
# cv2.destroyAllWindows()
