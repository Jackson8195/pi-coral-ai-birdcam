from flask import Flask, render_template, jsonify, current_app
import threading
import logging
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
    
    # Get the log file path from Flask's config
    log_file_path = current_app.config.get('LOG_FILE_PATH', '')
    
    if not log_file_path:
        return bird_counts  # No log file path set
    
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(",")  # Split by comma (timestamp,bird)
                if len(parts) >= 2:
                    bird = parts[1]  # Bird name is in the second column
                    bird_counts[bird] += 1
    except IOError:
        print("Error reading log file.")
        return {}

    return bird_counts

@app.route('/')
def index():
    bird_counts = parse_log()
    return render_template('index.html', bird_counts=bird_counts)

@app.route('/api/bird_counts_raw')
def get_bird_data():
    return jsonify(parse_log())

@app.route('/about')
def about():
    return 'This is the about page'

def run_flask():
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def start_flask_server():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()