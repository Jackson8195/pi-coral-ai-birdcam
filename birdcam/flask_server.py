from flask import Flask, render_template, jsonify, current_app
import threading
from collections import defaultdict

app = Flask(__name__)
'''
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

@app.route('/api/bird_counts')
def get_bird_counts():
    return jsonify(parse_log())
'''
def run_flask():
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def start_flask_server():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()