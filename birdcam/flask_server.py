from flask import Flask, render_template, jsonify, current_app, send_from_directory
import threading
import logging
import os
from collections import defaultdict

app = Flask(__name__)

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


@app.route('/images<storage_folder>/<bird>')
def serve_bird_images(storage_folder, bird):
    if not os.path.exists(storage_folder):
        return "No storage folder found.", 404

    # Filter images by bird name in filename
    images = [f for f in os.listdir(storage_folder) if bird.lower().replace(" ", "_") in f.lower()]
    print(f"DEBUG: Found Images = {images}")

    return render_template('image_gallery.html', bird=bird, storage_folder=storage_folder, images=images)

@app.route('/images<storage_folder>/<filename>')
def serve_image(storage_folder, filename):
    if os.path.exists(os.path.join(storage_folder, filename)):
        return send_from_directory(storage_folder, filename)
    else:
        return "Image not found", 404

@app.route('/api/bird_counts_raw')
def get_bird_data():
    return jsonify(parse_log())

def run_flask():
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def start_flask_server():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()