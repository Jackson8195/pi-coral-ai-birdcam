from flask import Flask, render_template, jsonify, current_app, send_from_directory, request
import threading
import logging
import os
import re
import time
import json
import shutil
from collections import defaultdict
from datetime import date

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# Set Flask to log to its own file
def configure_logging():
    """Configures Flask to log to a separate file."""
    flask_log_file = app.config.get('FLASK_LOG_FILE_PATH', '')
    # Create a new log handler for Flask
    handler = logging.FileHandler(flask_log_file)
    handler.setLevel(logging.INFO)
    # Get Flask's logger and remove any previous handlers
    flask_logger = logging.getLogger('werkzeug')  # This is Flask's default request logger
    flask_logger.handlers.clear()  # Remove existing handlers
    flask_logger.addHandler(handler)  # Add our custom handler
    # Optionally, disable propagation to the root logger
    flask_logger.propagate = False

def parse_log():
    bird_counts = defaultdict(int)
    # Get the bird log txt file path from config in bird_classify
    log_file_path = current_app.config.get('LOG_FILE_PATH', '')
   
    if not log_file_path:
        return bird_counts  # No log file path set
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                if "Results:" in line:
                    bird = line.split("Results:")[-1].strip()
                    bird_counts[bird] += 1
    except IOError:
        print("Error reading log file.")
        return {}
    return bird_counts

@app.route('/')
def index():
    bird_counts = parse_log()
    # Get the bird images folder path from config in bird_classify
    storage_folder = current_app.config.get('STORAGE_PATH','')
    return render_template('index.html', bird_counts=bird_counts, storage_folder=storage_folder)

@app.route('/bird/<bird>')
def serve_bird_images(bird):
    storage_folder = current_app.config.get('STORAGE_PATH','')
    
    if not os.path.exists(storage_folder):
        print(f"DEBUG: Storage folder not found at {storage_folder}")
        return f"No storage folder found at {storage_folder}.", 404
        
    all_files = os.listdir(storage_folder)

    # Keep spaces in the search term since filenames have spaces
    search_term = bird.lower()
    print(f"DEBUG: Searching for files containing '{search_term}'")
    
    # Find all files containing the bird name (case insensitive)
    images = [f for f in all_files if search_term in f.lower()]

    #send data to template
    return render_template('image_gallery.html', bird=bird, images=images)

@app.route('/images/<filename>')
def serve_image(filename):
    storage_folder = current_app.config.get('STORAGE_PATH','')
    
    if not os.path.exists(storage_folder):
        return f"No storage folder found at {storage_folder}.", 404
        
    if os.path.exists(os.path.join(storage_folder, filename)):
        return send_from_directory(storage_folder, filename)
    else:
        return f"Image not found: {filename}", 404

@app.route('/api/bird_counts_raw')
def get_bird_data():
    return jsonify(parse_log())

@app.route('/api/latest_image')
def get_latest_image():
    storage_folder = current_app.config.get('STORAGE_PATH', '')
    bird_filters = request.args.getlist('birds[]')

    files = [f for f in os.listdir(storage_folder)
             if f.startswith('img-') and f.endswith(('.png', '.jpg', '.jpeg'))]

    if bird_filters:
        files = [f for f in files
                 if any(bf.lower().replace(' ', '') in f.lower().replace(' ', '') for bf in bird_filters)]

    if not files:
        return jsonify({'filename': None, 'bird': None}), 404

    def ts(name):
        m = re.search(r'(\d{10,})\.', name)
        return int(m.group(1)) if m else 0

    latest = max(files, key=ts)
    return jsonify({'filename': latest, 'bird': extract_bird_name(latest)})

@app.route('/api/stats')
def get_stats():
    log_file_path = current_app.config.get('LOG_FILE_PATH', '')
    today_str = date.today().strftime('%Y-%m-%d')
    today_counts = defaultdict(int)
    last_detection = None

    if log_file_path:
        try:
            with open(log_file_path, 'r') as f:
                for line in f:
                    if 'Results:' not in line:
                        continue
                    if not line.startswith(today_str):
                        continue
                    bird = line.split('Results:')[-1].strip()
                    today_counts[bird] += 1
                    try:
                        last_detection = line[:19]
                    except Exception:
                        pass
        except IOError:
            pass

    total = sum(today_counts.values())
    species_count = len(today_counts)
    most_frequent = max(today_counts, key=today_counts.get) if today_counts else None
    most_frequent_count = today_counts[most_frequent] if most_frequent else 0

    return jsonify({
        'total_today': total,
        'species_today': species_count,
        'most_frequent': most_frequent,
        'most_frequent_count': most_frequent_count,
        'last_detection': last_detection
    })

import threading

@app.route('/shutdown', methods=['POST'])
def close_application():
    """Gracefully stop the bird_classify script and shut down the Raspberry Pi."""
    os.system("sudo shutdown now")  # Shutdown the Raspberry Pi
    return "Shutting down...", 200

hue_lights_paused = False

@app.route('/api/hue_pause', methods=['POST'])
def pause_hue_lights():
    global hue_lights_paused
    data = None
    try:
        data = request.get_json()
    except Exception:
        pass
    if data and 'paused' in data:
        hue_lights_paused = data['paused']
        print(f"Hue lights paused: {hue_lights_paused}")
        return jsonify({'status': 'ok', 'paused': hue_lights_paused})
    return jsonify({'status': 'error'}), 400

@app.route('/api/hue_pause', methods=['GET'])
def get_hue_pause():
    global hue_lights_paused
    return jsonify({'paused': hue_lights_paused})

def is_hue_lights_paused():
    global hue_lights_paused
    return hue_lights_paused

TRAINING_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training_data')


def get_labeled_filenames():
    """Return set of filenames that have already been labeled in training_data/."""
    labeled = set()
    if not os.path.isdir(TRAINING_DATA_DIR):
        return labeled
    for bird_dir in os.listdir(TRAINING_DATA_DIR):
        bird_path = os.path.join(TRAINING_DATA_DIR, bird_dir)
        if not os.path.isdir(bird_path):
            continue
        for id_type in ('PositiveID', 'NegativeID'):
            id_path = os.path.join(bird_path, id_type)
            if os.path.isdir(id_path):
                for f in os.listdir(id_path):
                    if f.endswith(('.png', '.jpg', '.jpeg')):
                        labeled.add(f)
    return labeled


def get_training_counts():
    """Return dict of {bird: {positive: N, negative: N}} from training_data folder."""
    counts = {}
    if not os.path.isdir(TRAINING_DATA_DIR):
        return counts
    for bird_dir in sorted(os.listdir(TRAINING_DATA_DIR)):
        bird_path = os.path.join(TRAINING_DATA_DIR, bird_dir)
        if not os.path.isdir(bird_path):
            continue
        pos_dir = os.path.join(bird_path, 'PositiveID')
        neg_dir = os.path.join(bird_path, 'NegativeID')
        pos = len([f for f in os.listdir(pos_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]) if os.path.isdir(pos_dir) else 0
        neg = len([f for f in os.listdir(neg_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]) if os.path.isdir(neg_dir) else 0
        if pos > 0 or neg > 0:
            counts[bird_dir] = {'positive': pos, 'negative': neg}
    return counts


def load_labels():
    """Load bird labels from the model label file."""
    labels_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'inat_bird_labels.txt')
    labels = []
    with open(labels_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.endswith('background'):
                continue
            # Format: "68 Cardinalis cardinalis (Northern Cardinal)"
            # Extract the friendly name from parentheses
            if '(' in line and ')' in line:
                common = line[line.index('(') + 1:line.index(')')]
                scientific = line.split(' ', 1)[1].split('(')[0].strip()
                labels.append({'common': common, 'scientific': scientific})
    return labels


@app.route('/training')
def training_dashboard():
    counts = get_training_counts()
    storage_folder = current_app.config.get('STORAGE_PATH', '')
    # Get list of bird species with images in current run
    bird_species = []
    if storage_folder and os.path.isdir(storage_folder):
        bird_counts = parse_log()
        bird_species = list(bird_counts.keys())
    return render_template('training.html', training_counts=counts, bird_species=bird_species)


@app.route('/training/images/<bird>')
def training_bird_images(bird):
    """Show images from current run for a specific bird, ready for labeling."""
    storage_folder = current_app.config.get('STORAGE_PATH', '')
    if not storage_folder or not os.path.isdir(storage_folder):
        return "No storage folder found.", 404
    all_files = os.listdir(storage_folder)
    search_term = bird.lower()
    images = [f for f in all_files if search_term in f.lower() and f.endswith(('.png', '.jpg', '.jpeg'))]
    labeled = get_labeled_filenames()
    return render_template('training_select.html', bird=bird, images=images, labeled=labeled)


def extract_bird_name(filename):
    """Extract bird name from filename like 'img-NorthernCardinal0012345678.png'."""
    name = os.path.splitext(filename)[0]  # strip extension
    name = re.sub(r'^img-', '', name)      # strip img- prefix
    name = re.sub(r'\d{10,}$', '', name)   # strip trailing timestamp digits
    # Insert spaces before uppercase letters (PascalCase -> spaced)
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)
    return name.strip() if name.strip() else None


@app.route('/training/label/<filename>')
def training_label_image(filename):
    """Show the labeling interface for a specific image."""
    is_labeled = filename in get_labeled_filenames()
    detected_bird = extract_bird_name(filename)
    return render_template('training_label.html', filename=filename,
                           is_labeled=is_labeled, detected_bird=detected_bird or '')


@app.route('/api/training/labels')
def api_training_labels():
    """Return all bird labels for autocomplete."""
    return jsonify(load_labels())


@app.route('/api/training/save', methods=['POST'])
def api_training_save():
    """Save a labeled training image with bounding box annotation."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    filename = data.get('filename')
    label = data.get('label')
    bbox = data.get('bbox')  # {x, y, width, height} as ratios 0-1
    correct_id = data.get('correct_id', True)

    if not all([filename, label, bbox]):
        return jsonify({'error': 'Missing required fields: filename, label, bbox'}), 400

    storage_folder = current_app.config.get('STORAGE_PATH', '')
    src_path = os.path.join(storage_folder, filename)
    if not os.path.isfile(src_path):
        return jsonify({'error': f'Source image not found: {filename}'}), 404

    # Sanitize label for folder name
    safe_label = label.replace('/', '-').replace('\\', '-')
    id_folder = 'PositiveID' if correct_id else 'NegativeID'
    dest_dir = os.path.join(TRAINING_DATA_DIR, safe_label, id_folder)
    os.makedirs(dest_dir, exist_ok=True)

    # Copy image
    dest_path = os.path.join(dest_dir, filename)
    shutil.copy2(src_path, dest_path)

    # Save annotation alongside image
    annotation = {
        'filename': filename,
        'label': label,
        'correct_id': correct_id,
        'bbox': bbox
    }
    annotation_path = os.path.splitext(dest_path)[0] + '.json'
    with open(annotation_path, 'w') as f:
        json.dump(annotation, f, indent=2)

    return jsonify({'status': 'ok', 'saved_to': dest_path})


@app.route('/training/data/<bird>/<id_type>/<filename>')
def serve_training_image(bird, id_type, filename):
    """Serve images from the training data folder."""
    img_dir = os.path.join(TRAINING_DATA_DIR, bird, id_type)
    if os.path.isfile(os.path.join(img_dir, filename)):
        return send_from_directory(img_dir, filename)
    return "Image not found", 404


def run_flask():
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_flask_server():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()