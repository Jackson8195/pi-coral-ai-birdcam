#!/usr/bin/bash

# Copyright 2019 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Birdcam runner
# Adapted by Pete Milne from Coral Smart Bird Feeder Script.
# Automates running the bird_classify code.

# Cleanup function to close MongoDB client connection
cleanup() {
    if [ -n "${mongo_pid}" ]; then
        echo "Closing MongoDB client connection..."
        kill "${mongo_pid}" >/dev/null 2>&1
        wait "${mongo_pid}" >/dev/null 2>&1
        echo "MongoDB client connection closed."
    fi
}

# Trap EXIT signal to call the cleanup function
trap cleanup EXIT

# Create a temp subdir in /tmp to store bird images and logs
tmp_dir=$(mktemp -d -t "birdcam-$(date +%Y-%m-%d)-XXXXXXXXXX")

# Source the ~/.bash_profile to set environment variables (MongoDB password stored in ~/.bash_profile)
source ~/.bash_profile

echo "$tmp_dir"

cd /home/pi/pi-coral-ai-birdcam/birdcam || exit

# Run bird_classify.py in the background and store its process ID
python3 bird_classify.py \
    --model models/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite \
    --labels models/inat_bird_labels.txt \
    --top_k 1 \
    --threshold 0.85 \
    --storage "$tmp_dir" \
    --visit_interval 10 &

# Store the process ID of the last background command (Python script)
mongo_pid=$!

# Wait for the Python script to finish
wait "${mongo_pid}"
