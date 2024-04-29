#!/usr/bin/python3

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Coral Smart Bird Feeder

Adapted by Peter Milne

Uses ClassificationEngine from the EdgeTPU API to analyse birds in
camera video frames. Stores image of any bird visits and logs time and species.

Users define model, labels file, storage path, and
optionally can set this to training mode for collecting images for a custom
model.

"""
import argparse
import time
import logging
import threading
import datetime
import phillips_hue
from PIL import Image
from collections import Counter
from phue import Bridge

from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.adapters import common
from pycoral.adapters.classify import get_classes

import gstreamer
import mongodb

#connect to and ping the Mongo DB
mongodb.mongoDB_connect()

b = Bridge('192.168.0.156')

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
b.connect()


def save_data(image, results, path, ext='png'):
    """Saves camera frame and model inference results
    to user-defined storage directory."""
    tag = '%010d' % int(time.monotonic()*1000)
    name = '%s/img-%s.%s' % (path, tag, ext)
    image.save(name)
    print('Frame saved as: %s' % name)
    logging.info('Image: %s Results: %s', tag, results)


def print_results(start_time, last_time, end_time, results):
    """Print results to terminal for debugging."""
    inference_rate = ((end_time - start_time) * 1000)
    fps = (1.0/(end_time - last_time))
    print('\nInference: %.2f ms, FPS: %.2f fps' % (inference_rate, fps))
    for label, score in results:
        print(' %s, score=%.2f' % (label, score))


def do_training(results, last_results, top_k):
    """Compares current model results to previous results and returns
    true if at least one label difference is detected. Used to collect
    images for training a custom model."""
    new_labels = [label[0] for label in results]
    old_labels = [label[0] for label in last_results]
    shared_labels = set(new_labels).intersection(old_labels)
    if len(shared_labels) < top_k:
        print('Difference detected')
        return True
    return False


def user_selections():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True,
                        help='.tflite model path')
    parser.add_argument('--labels', required=True,
                        help='label file path')
    parser.add_argument('--videosrc', help='Which video source to use',
                        default='/dev/video0')
    parser.add_argument('--top_k', type=int, default=1,
                        help='number of classes with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.4,
                        help='class score threshold')
    parser.add_argument('--storage', required=True,
                        help='File path to store images and results')
    parser.add_argument('--print', default=False, required=False,
                        help='Print inference results to terminal')
    parser.add_argument('--training', action='store_true',
                        help='Training mode for image collection')
    parser.add_argument('--visit_interval', action='store', type=int, default=2,
                        help='Minimum interval between bird visits')
    args = parser.parse_args()
    return args


def main():
    """Creates camera pipeline, and pushes pipeline through ClassificationEngine
    model. Logs results to user-defined storage. Runs either in training mode to
    gather images for custom model creation or capture mode that records images
    of bird visits if a model label is detected."""
    args = user_selections()
    print(args)
    print("Loading %s with %s labels." % (args.model, args.labels))
    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    labels = read_label_file(args.labels)
    input_tensor_shape = interpreter.get_input_details()[0]['shape']
    if (input_tensor_shape.size != 4 or
            input_tensor_shape[0] != 1):
        raise RuntimeError(
            'Invalid input tensor shape! Expected: [1, height, width, channel]')

    output_tensors = len(interpreter.get_output_details())
    if output_tensors != 1:
        raise ValueError(
            ('Classification model should have 1 output tensor only!'
             'This model has {}.'.format(output_tensors)))
    storage_dir = args.storage
    # Initialize logging file
    logging.basicConfig(filename='%s/results.log' % storage_dir,
                        format='%(asctime)s-%(message)s',
                        level=logging.DEBUG)
    last_time = time.monotonic()
    last_results = [('label', 0)]
    visitors = []
    hueVisitors = []
    hue_birds = [
        ['Cardinalis cardinalis (Northern Cardinal)', 0, 255, 255],
        ['Cyanocitta cristata (Blue Jay)', 45000, 255, 255]
    ]

    DURATION = args.visit_interval
    timer = False
    hueTimer = False

    def timed_event():
        nonlocal timer
        timer = True
        threading.Timer(DURATION, timed_event).start()

    def hue_timed_event():
        nonlocal hueTimer
        hueTimer = True
        threading.Timer(3, hue_timed_event).start()

    timed_event()
    hue_timed_event()

    def user_callback(image, svg_canvas):
        nonlocal last_time
        nonlocal last_results
        nonlocal visitors
        nonlocal timer
        nonlocal hueTimer
        nonlocal hue_birds
        nonlocal hueVisitors
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%m/%d/%Y %H:%M:%S")
        start_time = time.monotonic()
        common.set_resized_input(
            interpreter, image.size,
            lambda size: image.resize(size, Image.NEAREST))
        interpreter.invoke()
        results = get_classes(interpreter, args.top_k, args.threshold)
        end_time = time.monotonic()
        play_sounds = [labels[i] for i, score in results]
        results = [(labels[i], score) for i, score in results]
        if args.print:
            print_results(start_time, last_time, end_time, results)

        if args.training:
            if do_training(results, last_results, args.top_k):
                save_data(image, results, storage_dir)
        else:
            # Custom model mode:
            if len(results):
                visitor = results[0][0]
                
                if visitor not in EXCLUSIONS:
                    #set countertop lights to bird color
                    if hueTimer:
                        print("Hue Timer up!!!!!!!!")
                        counter = Counter(hueVisitors)
                        # Get the most common element over the timer duration and its count
                        most_common_bird = counter.most_common(1)[0]
                        print(most_common_bird, "count: ", counter)
                        print("type is: ",type(most_common_bird))
                        hueTimer = False
                        '''
                        if any(most_common_bird == entry[0] for entry in hue_birds):
                            bird_lookup = [entry for entry in hue_birds if entry[0] == most_common_bird]
                            b.set_light('Countertop Lights', {'hue': bird_lookup[1], 'sat': bird_lookup[2], 'bri': bird_lookup[3]})
                            hueVisitors.append(visitor)
                        '''
                    else:
                        hueVisitors.append(visitor)
                        print("Hue Timer Running..")
                        print(hueVisitors)
                        pass
                        

                    # If visit interval has past, clear visitors list
                    if timer:
                        print("next visit...")
                        visitors.clear()
                        timer = False
                    # If this is a new visit, add bird to visitors list
                    # so we don't keep taking the same image
                    if visitor not in visitors:
                        print("Visitor: ", visitor)
                        print("Score: ", results[0][1])
                        print("Visited at: ", formatted_time)
                        save_data(image,  visitor, storage_dir)
                        mongodb.mongo_insert(visitor, results[0][1], formatted_time)
                        visitors.append(visitor)

        last_results = results
        last_time = end_time
    gstreamer.run_pipeline(user_callback, videosrc=args.videosrc)


if __name__ == '__main__':
    # Add to this list for false positives for your camera
    EXCLUSIONS = ['background',
                 'Branta canadensis (Canada Goose)',
                 "Cyanocitta stelleri (Steller's Jay)"]
    main()
