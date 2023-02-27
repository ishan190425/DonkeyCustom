#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 10:44:24 2017

@author: wroscoe
"""

import time
import numpy as np
import logging
from threading import Thread
from .memory import Memory
from prettytable import PrettyTable
import traceback
import donkeycar
import os
import PIL
import pickle
logger = logging.getLogger(__name__)


class PartProfiler:
    def __init__(self):
        self.records = {}
        self.fps = []
        self.old_time = time.time()

    def profile_fps(self):
        newTime = time.time()
        processTime = newTime - self.old_time
        fps = 1.0 / processTime
        self.fps.append(fps)
        self.old_time = newTime

    def profile_part(self, p,threaded = False):
        self.records[p] = { "times" : [] }
        self.records[p]['threaded'] = threaded

    def on_part_start(self, p):
        self.records[p]['times'].append(time.time())
        

    def on_part_finished(self, p):
        now = time.time()
        prev = self.records[p]['times'][-1]
        delta = now - prev
        thresh = 0.000001
        if delta < thresh or delta > 100000.0:
            delta = thresh
        self.records[p]['times'][-1] = delta

    def report(self):
        logger.info("Part Profile Summary: (times in ms)")
        pt = PrettyTable()
        field_names = ["part","threaded", "max", "min", "avg"]
        pctile = [50, 90, 99, 99.9]
        pt.field_names = field_names + [str(p) + '%' for p in pctile]
        for p, val in self.records.items():
            # remove first and last entry because you there could be one-off
            # time spent in initialisations, and the latest diff could be
            # incomplete because of user keyboard interrupt
            arr = val['times'][1:-1]
            if len(arr) == 0:
                continue
            threaded = val['threaded']
            row = [p.__class__.__name__,
                   f"{threaded}",
                   "%.2f" % (max(arr) * 1000),
                   "%.2f" % (min(arr) * 1000),
                   "%.2f" % (sum(arr) / len(arr) * 1000)]
            row += ["%.2f" % (np.percentile(arr, p) * 1000) for p in pctile]
            pt.add_row(row)
        arr = self.fps
        row = ["FPS","False","%.2f" % (max(arr)),
                   "%.2f" % (min(arr)),
                   "%.2f" % (sum(arr) / len(arr))]
        row += ["%.2f" % (np.percentile(arr, p)) for p in pctile]
        pt.add_row(row)
        logger.info('\n' + str(pt))


class Vehicle:
    def __init__(self, mem=None):

        if not mem:
            mem = Memory()
        self.mem = mem
        self.parts = []
        self.on = True
        self.threads = []
        self.profiler = PartProfiler()
        self.cfg = donkeycar.load_config()
        self.STOP_SIGN_DETECTOR = self.cfg.STOP_SIGN_DETECTOR

    def add(self, part, inputs=[], outputs=[],
            threaded=False, run_condition=None):
        """
        Method to add a part to the vehicle drive loop.

        Parameters
        ----------
            part: class
                donkey vehicle part has run() attribute
            inputs : list
                Channel names to get from memory.
            outputs : list
                Channel names to save to memory.
            threaded : boolean
                If a part should be run in a separate thread.
            run_condition : str
                If a part should be run or not
        """
        assert type(inputs) is list, "inputs is not a list: %r" % inputs
        assert type(outputs) is list, "outputs is not a list: %r" % outputs
        assert type(threaded) is bool, "threaded is not a boolean: %r" % threaded

        p = part
        
        logger.info('Adding part {}.'.format(p.__class__.__name__))
        entry = {}
        entry['part'] = p
        entry['inputs'] = inputs
        entry['outputs'] = outputs
        entry['run_condition'] = run_condition

        if threaded:
            t = Thread(target=part.update, args=())
            t.daemon = True
            entry['thread'] = t

        self.parts.append(entry)
        self.profiler.profile_part(part,threaded)

    def remove(self, part):
        """
        remove part form list
        """
        self.parts.remove(part)

    def start(self, rate_hz=10, max_loop_count=None, verbose=False):
        """
        Start vehicle's main drive loop.

        This is the main thread of the vehicle. It starts all the new
        threads for the threaded parts then starts an infinite loop
        that runs each part and updates the memory.

        Parameters
        ----------

        rate_hz : int
            The max frequency that the drive loop should run. The actual
            frequency may be less than this if there are many blocking parts.
        max_loop_count : int
            Maximum number of loops the drive loop should execute. This is
            used for testing that all the parts of the vehicle work.
        verbose: bool
            If debug output should be printed into shell
        """

        try:

            self.on = True

            for entry in self.parts:
                if entry.get('thread'):
                    # start the update thread
                    entry.get('thread').start()

            # wait until the parts warm up.
            logger.info('Starting vehicle at {} Hz'.format(rate_hz))

            loop_count = 0
            while self.on:
                start_time = time.time()
                loop_count += 1

                self.update_parts()

                # stop drive loop if loop_count exceeds max_loopcount
                if max_loop_count and loop_count > max_loop_count:
                    self.on = False

                sleep_time = 1.0 / rate_hz - (time.time() - start_time)
                if sleep_time > 0.0:
                    time.sleep(sleep_time)
                else:
                    # print a message when could not maintain loop rate.
                    if verbose:
                        logger.info('WARN::Vehicle: jitter violation in vehicle loop '
                              'with {0:4.0f}ms'.format(abs(1000 * sleep_time)))

                if verbose and loop_count % 200 == 0:
                    self.profiler.report()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            traceback.print_exc()
        finally:
            self.stop()

    def update_parts(self):
        '''
        loop over all parts
        '''
        for entry in self.parts:

            run = True
            # check run condition, if it exists
            if entry.get('run_condition'):
                run_condition = entry.get('run_condition')
                run = self.mem.get([run_condition])[0]
            
            if run:
                # get part
                p = entry['part']
                # start timing part run
                self.profiler.on_part_start(p)
                if (self.STOP_SIGN_DETECTOR and type(p)== donkeycar.parts.object_detector.stop_sign_detector_Tensorflow.StopSignDetector):
                    if os.path.exists("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/stop.pickle"):
                        print("Found Stop Sign")
                        with open('/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/stop.pickle',"rb") as file:
                            outputs = pickle.load(file)
                            self.mem.put(entry['outputs'], outputs)
                    img = self.mem.get_old_image() 
                    # img = np.array(img)
                    # np.save("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/img.npy",img)

                    im = PIL.Image.fromarray(img)
                    im.save("/home/pi/projects/DonkeyCustom/donkeycar/parts/object_detector/img.jpg",quality=50)
                else:
                    # get inputs from memory
                    inputs = self.mem.get(entry['inputs'])
                    # run the part
                    if entry.get('thread'):
                        outputs = p.run_threaded(*inputs)
                    else:
                        outputs = p.run(*inputs)

                    # save the output to memory
                    if outputs is not None:
                        self.mem.put(entry['outputs'], outputs)
                    if type(p) == donkeycar.parts.camera.Webcam:
                        img = p.get_old_image()
                        self.mem.add_old_image(img)
                    # finish timing part run
                self.profiler.on_part_finished(p)
                self.profiler.profile_fps()

    def stop(self):        
        logger.info('Shutting down vehicle and its parts...')
        for entry in self.parts:
            try:
                entry['part'].shutdown()
            except AttributeError:
                # usually from missing shutdown method, which should be optional
                pass
            except Exception as e:
                logger.error(e)

        self.profiler.report()
